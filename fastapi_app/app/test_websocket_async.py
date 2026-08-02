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
    async with websockets.connect(owner_url) as ws:
        # Should get sync messages again
        # The user was 'disconnected' but not removed yet, so it should re-join
        msg = await asyncio.wait_for(recv_json(ws), timeout=5)
        assert msg["type"] == "lobby_sync"

        # Verify status is connected (implicit in lobby_sync if they appear)
        assert any(u["user_id"] == owner_cookies["user_id"] and u["status"] == "connected" for u in msg["users"])


@pytest.mark.asyncio
async def test_manual_ownership_transfer(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    async with httpx.AsyncClient(base_url=http_base_url) as client:
        # Create lobby as owner
        response = await client.post(
            "/api/create_lobby",
            json={"user_name": "owner", "lobby_name": "transfer test", "lobby_theme": "rock", "lobby_description": "test"},
        )
        owner_cookies = client.cookies
    lobby_id = response.json()["lobby_id"]
    lobby_secret = response.json()["lobby_secret"]

    # User 2 joins
    async with httpx.AsyncClient(base_url=http_base_url) as c:
        await c.get("/api/ping")
        user2_cookies = c.cookies
        
    owner_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=owner&user_id={owner_cookies['user_id']}&user_secret={owner_cookies['user_secret']}"
    user2_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=user2&user_id={user2_cookies['user_id']}&user_secret={user2_cookies['user_secret']}"

    async with websockets.connect(owner_url) as owner_ws, websockets.connect(user2_url) as user2_ws:
        # Consume initial sync messages for both
        for _ in range(3):
            await owner_ws.recv()
            await user2_ws.recv()
        
        # Owner transfers ownership
        await owner_ws.send(json.dumps({
            "type": "set_owner",
            "new_owner_id": user2_cookies["user_id"],
            "lobby_secret": lobby_secret
        }))
        
        # Owner should get a sync message indicating change
        while True:
            msg = await asyncio.wait_for(recv_json(owner_ws), timeout=5)
            if msg["type"] == "lobby_sync" and msg["author_id"] == user2_cookies["user_id"]:
                break
        
        # User2 should also get the sync message
        msg2 = await asyncio.wait_for(recv_json(user2_ws), timeout=5)
        assert msg2["type"] == "lobby_sync"
        assert msg2["author_id"] == user2_cookies["user_id"]


@pytest.mark.asyncio
async def test_chat_history_on_join(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    async with httpx.AsyncClient(base_url=http_base_url) as client:
        # Create lobby
        response = await client.post(
            "/api/create_lobby",
            json={"user_name": "owner", "lobby_name": "history test", "lobby_theme": "rock", "lobby_description": "test"},
        )
        owner_cookies = client.cookies
    lobby_id = response.json()["lobby_id"]

    # Prepare user URLs
    async with httpx.AsyncClient(base_url=http_base_url) as c:
        await c.get("/api/ping")
        owner_cookies = c.cookies
    async with httpx.AsyncClient(base_url=http_base_url) as c:
        await c.get("/api/ping")
        user2_cookies = c.cookies

    owner_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=owner&user_id={owner_cookies['user_id']}&user_secret={owner_cookies['user_secret']}"
    user2_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=user2&user_id={user2_cookies['user_id']}&user_secret={user2_cookies['user_secret']}"

    # Owner joins
    async with websockets.connect(owner_url) as owner_ws:
        # Consume sync
        for _ in range(3):
            await owner_ws.recv()
            
        # Owner sends a chat message
        await owner_ws.send(json.dumps({"type": "player_chat", "body": "Hello history!"}))
        
        # User2 joins
        async with websockets.connect(user2_url) as user2_ws:
            # 1. Sync
            await user2_ws.recv() 
            # 2. Player Chat History
            msg = await asyncio.wait_for(recv_json(user2_ws), timeout=5)
            assert msg["type"] == "player_chat_history"
            assert any(m["body"] == "Hello history!" for m in msg["messages"])


@pytest.mark.asyncio
async def test_manual_lobby_settings_change(server):
    http_base_url = server["http"]
    ws_base_url = server["ws"]

    async with httpx.AsyncClient(base_url=http_base_url) as client:
        # Create lobby as owner
        response = await client.post(
            "/api/create_lobby",
            json={"user_name": "owner", "lobby_name": "test lobby", "lobby_theme": "rock", "lobby_description": "test"},
        )
        owner_cookies = client.cookies
    lobby_id = response.json()["lobby_id"]
    lobby_secret = response.json()["lobby_secret"]

    # User 2 joins
    async with httpx.AsyncClient(base_url=http_base_url) as c:
        await c.get("/api/ping")
        user2_cookies = c.cookies
        
    owner_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=owner&user_id={owner_cookies['user_id']}&user_secret={owner_cookies['user_secret']}"
    user2_url = f"{ws_base_url}/api/join_lobby?lobby_id={lobby_id}&user_name=user2&user_id={user2_cookies['user_id']}&user_secret={user2_cookies['user_secret']}"

    async with websockets.connect(owner_url) as owner_ws, websockets.connect(user2_url) as user2_ws:
        # Consume initial sync messages for both
        for _ in range(3):
            await owner_ws.recv()
            await user2_ws.recv()
        
        # 1. Owner updates settings
        new_settings = {
            "type": "update_lobby_settings",
            "lobby_name": "updated name",
            "theme": "jazz",
            "description": "updated description",
            "lobby_secret": lobby_secret
        }
        await owner_ws.send(json.dumps(new_settings))
        
        # Verify update (owner and user2 receive sync)
        for ws in [owner_ws, user2_ws]:
            while True:
                msg = await asyncio.wait_for(recv_json(ws), timeout=5)
                if msg["type"] == "lobby_sync" and msg["lobby_name"] == "updated name":
                    assert msg["theme"] == "jazz"
                    assert msg["description"] == "updated description"
                    break
        
        # 2. User2 attempts update (unauthorized secret)
        invalid_settings = {
            "type": "update_lobby_settings",
            "lobby_name": "malicious update",
            "lobby_secret": "wrong_secret"
        }
        await user2_ws.send(json.dumps(invalid_settings))
        
        # Verify no sync message is received (timeout check)
        try:
            # We expect NO lobby_sync message, so waiting should time out
            await asyncio.wait_for(recv_json(user2_ws), timeout=2)
            pytest.fail("Unauthorized user should not have received a sync message")
        except asyncio.TimeoutError:
            pass # Expected behavior: no message received

