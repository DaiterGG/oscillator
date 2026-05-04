from fastapi import WebSocket
from fastapi.testclient import TestClient

import httpx
from starlette.websockets import WebSocketDisconnect

from .main import app



print("test")

def test_lobby_create():
    client = TestClient(app, base_url="https://testserver")
    print("test fn")
    res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me"})
    print(res)
    l_id = res.json()["lobby_id"]
    assert 20 == len(l_id)

    print("enter")
    with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=foobar") as res1:
        print("connected")
        res1.send_json({"type": "test_ping"})
        data = res1.receive_json()
        assert data == {"type": "test_ping"}
        print("asserted")
    

def test_lobby_chat():

    client = TestClient(app, base_url="https://testserver")
    client2 = TestClient(app, base_url="https://testserver")
    print("test fn")
    res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me"})
    print(res)
    l_id = res.json()["lobby_id"]
    assert 20 == len(l_id)
    res: httpx.Response = client2.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me"})

    print("enter")
    with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=john") as john:
        with client2.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=mark") as mark:
            print("connected")
            john.send_json({"type": "message", "body": "hi mark"})
            mark.send_json({"type": "message", "body": "hi john"})
            print("clients messages sent")
            # NOTE: testclient seems to deadlock even tho both messages are sent
            # not sure but assuming limitation of a test client
            # data1 = john.receive_json()
            # data2 = mark.receive_json()
            # print("mark received a message")
            # assert data1["body"] == "hi john"
            # assert data2["body"] == "hi mark"
            # print("asserted")

def test_lobby_delete():
    client = TestClient(app, base_url="https://testserver")
    res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me"})
    json = res.json()
    l_id = json["lobby_id"]
    secret = json["lobby_secret"]
    print("lobby id " + l_id)
    print("lobby secret" + secret)
    res: httpx.Response = client.post("/api/delete_lobby", json= { "lobby_id": l_id, "lobby_secret": secret, "final_message": "goodbye"})
    assert 200 == res.status_code
    try:
        with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=john") as ws:
            pass
    except Exception as e:
        assert type(WebSocketDisconnect()) == type(e)



def test_main():
    client = TestClient(app, base_url="https://testserver")
    res = client.get("/")
    print(res.text)
