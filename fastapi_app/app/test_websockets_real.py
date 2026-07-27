import asyncio
import httpx
import pytest
import websockets
import json

@pytest.mark.asyncio
async def test_lobby_chat():
    base_url = "http://127.0.0.1:8000"

    # NOTE: This test requires the server to be running on 127.0.0.1:8000
    async with httpx.AsyncClient(base_url=base_url) as client:
        res = await client.post(
            "/api/create_lobby",
            json={
                "user_name": "name1",
                "lobby_name": "join me",
                "lobby_theme": "rock",
                "lobby_description": "test",
            },
        )
        assert res.status_code == 200
        lobby_id = res.json()["lobby_id"]
        
        # Get cookies set by create_lobby
        cookies = client.cookies

    ws_url = f"ws://127.0.0.1:8000/api/join_lobby?lobby_id={lobby_id}"
    
    # Format cookies for headers
    cookie_header = "; ".join([f"{name}={value}" for name, value in cookies.items()])
    headers = {"Cookie": cookie_header}

    async def join_and_chat(nickname, message):
        async with websockets.connect(f"{ws_url}&user_name={nickname}", extra_headers=headers) as ws:
            # 1. Consume initial sync/history messages
            for _ in range(3):
                await ws.recv()
            
            # 2. Send chat message
            await ws.send(json.dumps({"type": "lobby_chat", "body": message}))
            
            # 3. Receive message back (the broadcast)
            return json.loads(await ws.recv())

    # Send and receive concurrently
    data1, data2 = await asyncio.gather(
        join_and_chat("john", "hi mark"),
        join_and_chat("mark", "hi john"),
    )

    assert data1["body"] == "hi mark"
    assert data2["body"] == "hi john"
