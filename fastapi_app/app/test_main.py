from uuid import uuid4
from fastapi import WebSocket
from fastapi.testclient import TestClient
from pydantic import UUID4
from starlette.websockets import WebSocketDisconnect
from starlette.testclient import WebSocketDenialResponse
import httpx

from .main import app



# def test_lobby_create():
#     client = TestClient(app, base_url="https://testserver")
#     print("test fn")
#     res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me", "lobby_theme": "rock", "lobby_description": "test"})
#     print(res)
#     l_id = res.json()["lobby_id"]
#     assert len(str(uuid4())) == len(l_id)

#     print("enter")
#     with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=foobar") as res1:
#         print("connected")
#         res1.send_json({"type": "test_ping"})
#         data = res1.receive_json()
#         assert data == {"type": "test_ping"}
#         print("asserted")
#         pass


# def test_lobby_chat():
#     client = TestClient(app, base_url="https://testserver")
#     client2 = TestClient(app, base_url="https://testserver")
#     print("test fn")
#     res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me", "lobby_theme": "rock", "lobby_description": "test"})
#     print(res)
#     l_id = res.json()["lobby_id"]
#     assert len(str(uuid4())) == len(l_id)
#     res: httpx.Response = client2.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me", "lobby_theme": "rock", "lobby_description": "test"})

#     print("enter")
#     with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=john") as john:
#         with client2.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=mark") as mark:
#             print("connected")
#             john.send_json({"type": "message", "body": "hi mark"})
#             mark.send_json({"type": "message", "body": "hi john"})
#             print("clients messages sent")
#             # NOTE: testclient seems to deadlock even tho both messages are sent
#             # not sure but assuming limitation of a test client
#             # data1 = john.receive_json()
#             # data2 = mark.receive_json()
#             # print("mark received a message")
#             # assert data1["body"] == "hi john"
#             # assert data2["body"] == "hi mark"
#             # print("asserted")


# def test_lobby_delete():
#     client = TestClient(app, base_url="https://testserver")
#     res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me", "lobby_theme": "rock", "lobby_description": "test"})
#     json = res.json()
#     l_id = json["lobby_id"]
#     secret = json["lobby_secret"]
#     print("lobby id " + l_id)
#     print("lobby secret" + secret)
#     res: httpx.Response = client.post("/api/delete_lobby", json= { "lobby_id": l_id, "lobby_secret": secret, "final_message": "goodbye"})
#     assert 200 == res.status_code
#     try:
#         with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=john") as ws:
#             pass
#     except Exception as e:
#         assert type(WebSocketDisconnect()) == type(e) or isinstance(e, WebSocketDenialResponse)

# def test_find():
#     client = TestClient(app, base_url="https://testserver")
#     client2 = TestClient(app, base_url="https://testserver")
#     print("test fn")
#     res: httpx.Response = client.post("/api/create_lobby", json= { "user_name": "name1", "lobby_name": "join me", "lobby_theme": "rock", "lobby_description": "test"})
#     print(res)
#     l_id: str = res.json()["lobby_id"]
#     print(l_id)
#     res: httpx.Response = client2.get("/api/find_lobby?lobby_page=1")
#     print(res.json())



# def test_main():
#     client = TestClient(app, base_url="https://testserver")
#     res = client.get("/api/ping")
#     assert 200 == res.status_code


# def test_lobby_details():
#     client = TestClient(app, base_url="https://testserver")
#     res = client.post("/api/create_lobby", json={"user_name": "owner_user", "lobby_name": "test details lobby", "lobby_theme": "rock", "lobby_description": "test"})
#     assert res.status_code == 200
#     l_id = res.json()["lobby_id"]
    
#     res_details = client.get(f"/api/lobby_details?lobby_id={l_id}")
#     assert res_details.status_code == 200
#     details = res_details.json()
#     assert details["lobby_name"] == "test details lobby"
#     assert details["author_name"] == "owner_user"
#     assert len(details["users"]) == 0

# def test_ownership_transfer():
#     client1 = TestClient(app, base_url="https://testserver") # Owner
#     client2 = TestClient(app, base_url="https://testserver") # Next user
    
#     # 1. Create Lobby
#     res = client1.post("/api/create_lobby", json={
#         "user_name": "owner", 
#         "lobby_name": "test lobby", 
#         "lobby_theme": "rock", 
#         "lobby_description": "test"
#     })
#     l_id = res.json()["lobby_id"]
    
#     # Get cookies from client1 (they were set during create_lobby)
#     cookies1 = client1.cookies
#     cookies2 = client2.cookies # Should be empty initially
    
#     # Force set cookies for client2 by making a dummy request
#     client2.get("/api/ping")
#     cookies2 = client2.cookies
    
    # # 2. Both join
    # with client1.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=owner", cookies=cookies1) as ws1:
    #     with client2.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=user2", cookies=cookies2) as ws2:
            
    #         # 3. Owner leaves
    #         ws1.close()
            
    #         # 4. Check user2 received owner_changed first
    #         msg = ws2.receive_json()
    #         # 5. Check user2 received owner_promoted
    #         msg = ws2.receive_json()
    #         assert msg["type"] == "owner_promoted"
    #         assert "new_secret" in msg

# def test_lobby_auto_delete():
#     client = TestClient(app, base_url="https://testserver")
    
#     # 1. Create Lobby
#     res = client.post("/api/create_lobby", json={
#         "user_name": "owner", 
#         "lobby_name": "test lobby", 
#         "lobby_theme": "rock", 
#         "lobby_description": "test"
#     })
#     l_id = res.json()["lobby_id"]
    
#     # 2. Join and leave
#     with client.websocket_connect(f"/api/join_lobby?lobby_id={l_id}&user_name=owner") as ws:
#         pass # Connection closed
    
    # # 3. Verify lobby is deleted
    # res = client.get(f"/api/lobby_details?lobby_id={l_id}")
    # assert res.status_code == 404
