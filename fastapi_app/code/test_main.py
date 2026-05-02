import time
from fastapi.testclient import TestClient

import httpx

from main import app, rnd_str

# NOTE: test with https for secure cookies
client = TestClient(app, base_url="https://testserver")

def test_lobby():
    res: httpx.Response = client.post("/api/create_lobby/", json= { "user_name": "name1", "lobby_name": "join me"})
    l_id = res.json()["lobby_id"]
    assert 20 == len(l_id)
    res: httpx.Response = client.post("/api/create_lobby/", json= { "user_name": "name1", "lobby_name": "join me"})
    l_id = res.json()["lobby_id"]
    assert 20 == len(l_id)
    print("enter")
    with client.websocket_connect("/api/connect/") as res1:
        print("connected")
        res1.send_json({"msg": "Hello WebSocket"})
        data = res1.receive_json()
        assert data == {"msg": "Hello WebSocket"}
        print("asserted")
        time.sleep(2)

    # response = res1.receive_text()
    # print(response)
    # res2 = client.websocket_connect(f"/api/connect")
    # res1.send({"type": "text_message", "message": "hi"})
    # res2.send_json({"type": "text_message", "message": "hello"})
    assert 1 == 0
    

def test_main():
    res = client.get("/")
    print(res.text)
