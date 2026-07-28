import asyncio
import json
import socket
from multiprocessing import Process
from uuid import UUID

import httpx
import pytest
import uvicorn
import websockets

from .main import app


HOST = "127.0.0.1"


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


def run_server(port: int) -> None:
    uvicorn.run(
        app,
        host=HOST,
        port=port,
        log_level="error",
    )


async def wait_for_server(port: int) -> None:
    for _ in range(50):
        try:
            reader, writer = await asyncio.open_connection(HOST, port)

            writer.close()
            await writer.wait_closed()

            return

        except ConnectionRefusedError:
            await asyncio.sleep(0.1)

    raise RuntimeError("Test server did not start")


@pytest.fixture
def server():
    port = get_free_port()

    process = Process(
        target=run_server,
        args=(port,),
        daemon=True,
    )

    process.start()

    # Wait until Uvicorn is ready
    asyncio.run(wait_for_server(port))

    yield {
        "http": f"http://{HOST}:{port}",
        "ws": f"ws://{HOST}:{port}",
    }

    process.terminate()
    process.join(timeout=5)

    if process.is_alive():
        process.kill()


# Helper function to receive and decode JSON messages
async def recv_json(ws):
    return json.loads(await ws.recv())


@pytest.mark.asyncio
async def test_lobby_chat(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    # ---------------------------------------------------------
    # Create lobby
    # ---------------------------------------------------------

    async with httpx.AsyncClient(
        base_url=http_base_url
    ) as client:

        response = await client.post(
            "/api/create_lobby",
            json={
                "user_name": "name1",
                "lobby_name": "join me",
                "lobby_theme": "rock",
                "lobby_description": "test",
            },
        )

    assert response.status_code == 200

    lobby_id = response.json()["lobby_id"]

    # Verify that the lobby ID is actually a UUID
    UUID(lobby_id)

    # We need to get the user_id and user_secret for the cookies
    async with httpx.AsyncClient(base_url=http_base_url) as client:
        # Create cookies by doing dummy requests
        await client.get("/api/ping")
        john_cookies = client.cookies
        
    async with httpx.AsyncClient(base_url=http_base_url) as client:
        await client.get("/api/ping")
        mark_cookies = client.cookies

    # ---------------------------------------------------------
    # Build WebSocket URLs
    # ---------------------------------------------------------

    john_url = (
        f"{ws_base_url}/api/join_lobby"
        f"?lobby_id={lobby_id}"
        f"&user_name=john"
        f"&user_id={john_cookies['user_id']}&user_secret={john_cookies['user_secret']}"
    )

    mark_url = (
        f"{ws_base_url}/api/join_lobby"
        f"?lobby_id={lobby_id}"
        f"&user_name=mark"
        f"&user_id={mark_cookies['user_id']}&user_secret={mark_cookies['user_secret']}"
    )

    async with (
        websockets.connect(john_url) as john,
        websockets.connect(mark_url) as mark,
    ):


        # -----------------------------------------------------
        # Send messages concurrently
        # -----------------------------------------------------

        await asyncio.gather(
            john.send(
                json.dumps(
                    {
                        "type": "player_chat",
                        "body": "hi mark",
                    }
                )
            ),
            mark.send(
                json.dumps(
                    {
                        "type": "player_chat",
                        "body": "hi john",
                    }
                )
            ),
        )

        # -----------------------------------------------------
        # Receive messages (Lobby Sync + Chat)
        # -----------------------------------------------------
        
        async def get_chat_message(ws, sender_name):
            while True:
                msg = await recv_json(ws)
                if msg.get("type") == "player_chat" and msg.get("user_name") != sender_name:
                    return msg
        
        john_message, mark_message = await asyncio.wait_for(asyncio.gather(
            get_chat_message(john, "john"),
            get_chat_message(mark, "mark"),
        ), timeout=10)

        # -----------------------------------------------------
        # Assert that each user received the other user's message
        # -----------------------------------------------------

        assert john_message["body"] == "hi john"
        assert mark_message["body"] == "hi mark"


@pytest.mark.asyncio
async def test_ownership_transfer_on_leave(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    async with httpx.AsyncClient(base_url=http_base_url) as client:
        response = await client.post(
            "/api/create_lobby",
            json={"user_name": "owner", "lobby_name": "transfer test", "lobby_theme": "rock", "lobby_description": "test"},
        )
        owner_cookies = client.cookies
    lobby_id = response.json()["lobby_id"]

    # Prepare URLs
    async with httpx.AsyncClient(base_url=http_base_url) as c:
        await c.get("/api/ping")
        user2_cookies = c.cookies

    owner_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=owner&user_id={owner_cookies['user_id']}&user_secret={owner_cookies['user_secret']}"
    user2_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=user2&user_id={user2_cookies['user_id']}&user_secret={user2_cookies['user_secret']}"

    async with websockets.connect(owner_url) as owner_ws, websockets.connect(user2_url) as user2_ws:
        # Consume sync messages
        for _ in range(3):
            await owner_ws.recv()
            await user2_ws.recv()
        
        # Owner leaves
        await owner_ws.close()
        
        # Wait for auto-transfer (sleep > 3s)
        await asyncio.sleep(4)
        
        # Check for owner_promoted
        try:
            while True:
                msg = await asyncio.wait_for(recv_json(user2_ws), timeout=5)
                if msg["type"] == "owner_promoted":
                    assert "new_secret" in msg
                    break
                else:
                    print(f"DEBUG: ignoring message type={msg['type']}")
        except asyncio.TimeoutError:
            pytest.fail("Timed out waiting for owner_promoted message")


@pytest.mark.asyncio
async def test_user_reconnection(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    async with httpx.AsyncClient(base_url=http_base_url) as client:
        response = await client.post(
            "/api/create_lobby",
            json={"user_name": "owner", "lobby_name": "reconnect test", "lobby_theme": "rock", "lobby_description": "test"},
        )
        owner_cookies = client.cookies
    lobby_id = response.json()["lobby_id"]

    owner_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=owner&user_id={owner_cookies['user_id']}&user_secret={owner_cookies['user_secret']}"

    # Connect
    async with websockets.connect(owner_url) as ws:
        # Consume sync
        await ws.recv()
        await ws.recv()
        await ws.recv()
        
        # Disconnect
        await ws.close()
        
    # Wait for the server to process the disconnection
    await asyncio.sleep(0.5)

    # Reconnect immediately (within 3s)
    try:
        async with websockets.connect(owner_url) as ws:
            # Should get sync messages again
            # The user was 'disconnected' but not removed yet, so it should re-join
            msg = await asyncio.wait_for(recv_json(ws), timeout=5)
            assert msg["type"] == "lobby_sync"

            # Verify status is connected (implicit in lobby_sync if they appear)
            assert any(u["user_id"] == owner_cookies["user_id"] and u["status"] == "connected" for u in msg["users"])
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"DEBUG: Connection closed with error: {e}")
        raise

