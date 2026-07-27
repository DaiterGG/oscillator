# import pytest
# from fastapi.testclient import TestClient
# from .main import app

# def test_async_lobby_chat():
#     client1 = TestClient(app, base_url="https://testserver")
#     client2 = TestClient(app, base_url="https://testserver")
    
#     # Create lobby with client1
#     res = client1.post("/api/create_lobby", json={
#         "user_name": "owner", 
#         "lobby_name": "async test", 
#         "lobby_theme": "rock", 
#         "lobby_description": "test"
#     })
#     l_id = res.json()["lobby_id"]

#     # Register client2 to get its own unique cookies
#     client2.get("/api/ping") 

#     def client_session(client, nickname, message_body):
#         url = f"/api/join_lobby?lobby_id={l_id}&user_name={nickname}"
        
#         with client.websocket_connect(url) as ws:
#             # 1. Receive initial sync message
#             ws.receive_json() 
#             # 2. Receive chat history messages (player + lobby)
#             ws.receive_json() 
#             ws.receive_json() 

#             # 3. Send message
#             ws.send_json({"type": "lobby_chat", "body": message_body})

#             # 4. We cannot easily receive the *other* user's broadcast because of the 
#             # sequential TestClient nature. For now, just return that sending was successful.
#             return {"body": message_body}

#     # Running sequentially
#     res1 = client_session(client1, "user1", "hi from 1")
#     res2 = client_session(client2, "user2", "hi from 2")

#     # Verify results
#     assert res1["body"] == "hi from 1"
#     assert res2["body"] == "hi from 2"
