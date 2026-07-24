import time
import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..model.lobbies import lobbies
from ..model.lobby import Lobby
from ..model.connected_user import ConnectedUser

router = APIRouter()

async def broadcast_lobby_sync(lobby: Lobby):
    user_list = []
    for uid, u in lobby.users.items():
        user_list.append({
            "user_id": uid,
            "user_name": u.user_name,
            "status": u.status,
            "join_time": u.join_time
        })
    
    for _, user in lobby.users.items():
        if user.status == "connected":
            await user.socket.send_json({
                "type": "lobby_sync",
                "users": user_list,
                "author_id": lobby.author.author_id,
                "lobby_name": lobby.lobby_name,
                "theme": lobby.theme,
                "description": lobby.description
            })

@router.websocket("/api/join_lobby")
async def join_lobby(ws: WebSocket):
    user = await parse_and_connect(ws)
    try:
        while True:
            await websocket_read_message(user)
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        async def delayed_disconnect():
            await asyncio.sleep(3)
            if user.status == "disconnected":
                try:
                    lobby = lobbies.get_or_status(user.lobby_id, 200)
                    u_id = user.socket.state.user_id

                    if u_id == lobby.author.author_id:
                        result = lobby.get_new_owner()
                        if result:
                            new_owner_id, new_owner_user, new_secret = result
                            lobby.transfer_ownership(new_owner_id, new_secret)
                            # Sync after ownership transfer
                            await broadcast_lobby_sync(lobby)

                    for other_id, other_user in lobby.users.items():
                        if other_id != u_id:
                            await other_user.socket.send_json({
                                "type": "user_left",
                                "user_id": u_id,
                                "user_name": user.user_name
                            })
                    
                    # Sync after leave
                    await broadcast_lobby_sync(lobby)
                except Exception as e:
                    print(f"Failed to notify other users of leave: {e}")
                await lobbies.disconnect_user(user.lobby_id, user.socket.state.user_id)

        user.status = "disconnected"
        user.reconnect_task = asyncio.create_task(delayed_disconnect())



async def parse_and_connect(ws: WebSocket) -> ConnectedUser:
    print("connecting")
    try:
        user_name = ws.query_params["user_name"]
        print(f"user {user_name} connecting")
        lobby_id = ws.query_params["lobby_id"]
        print(f"to lobby {lobby_id}")
        u_id = ws.cookies["user_id"]
        u_secret = ws.cookies["user_secret"]
    except:
        await ws.close()
        raise HTTPException(status_code=400, detail="credentials was not provided")

    # manually set state for ws://
    ws.state.user_id = u_id
    ws.state.user_secret = u_secret

    lobby = lobbies.get_or_status(lobby_id, 400)

    password = ws.query_params.get("password")
    if lobby.is_password_protected() and lobby.password != password:
         raise HTTPException(status_code=401, detail="wrong password")

    # Handle reconnection
    if u_id in lobby.users:
        user = lobby.users[u_id]
        if user.status == "disconnected":
            print(f"Reconnecting user {u_id}")
            if user.reconnect_task:
                user.reconnect_task.cancel()
            user.status = "connected"
            user.socket = ws
            await ws.accept()
            
            # Send sync and chat history to the reconnected user
            await broadcast_lobby_sync(lobby)
            for m in lobby.player_history:
                await ws.send_json(m)
            for m in lobby.lobby_history:
                await ws.send_json(m)
            
            return user
        else:
            raise HTTPException(status_code=409, detail="you are already connected in a different tab")

    await ws.accept()

    connected = ConnectedUser(user_name=user_name, lobby_id=lobby_id, socket=ws)

    lobby.users[u_id] = connected

    # Sync after join
    await broadcast_lobby_sync(lobby)
    
    # Send chat history
    for m in lobby.player_history:
        await ws.send_json(m)
    for m in lobby.lobby_history:
        await ws.send_json(m)

    # Notify other users in the lobby that a new user joined
    for other_id, other_user in lobby.users.items():
        if other_id != u_id:
            try:
                await other_user.socket.send_json({
                    "type": "user_joined",
                    "user_id": u_id,
                    "user_name": user_name,
                    "join_time": connected.join_time
                })
            except Exception as e:
                print(f"Failed to notify user {other_user.user_name} of join: {e}")

    return connected

async def websocket_read_message(user: ConnectedUser):

    mes = await user.socket.receive_json()
    print("read message")
    if mes["type"] in ["player_chat", "lobby_chat"]:
        mes["stamp"] = str(time.time())
        mes["user_name"] = user.user_name
        mes["user_id"] = user.socket.state.user_id
        lobby = lobbies.get_or_status(user.lobby_id, 400)
        
        if mes["type"] == "player_chat":
            lobby.player_history.append(mes)
        else:
            lobby.lobby_history.append(mes)
            
        for _, other_user in lobby.users.items():
            print(f"sending {mes['type']} from {user.user_name} to {other_user.user_name}")
            await other_user.socket.send_json(mes)
            print(f"{mes['type']} sent from {user.user_name} to {other_user.user_name}")

    elif mes["type"] == "test_ping":
        await user.socket.send_json(mes)
    elif mes["type"] == "update_lobby_settings":
        lobby = lobbies.get_or_status(user.lobby_id, 400)
        # Check if the requester is the current owner using the lobby_secret
        if user.socket.state.user_id == lobby.author.author_id and user.socket.state.user_secret == lobby.author.lobby_secret:
            if "lobby_name" in mes:
                lobby.lobby_name = mes["lobby_name"] if mes["lobby_name"].strip() else "None"
            if "theme" in mes:
                lobby.theme = mes["theme"] if mes["theme"].strip() else "None"
            if "description" in mes:
                lobby.description = mes["description"] if mes["description"].strip() else "None"
            if "password" in mes:
                lobby.password = mes["password"]
            
            await broadcast_lobby_sync(lobby)

    elif mes["type"] == "set_owner":
        lobby = lobbies.get_or_status(user.lobby_id, 400)
        # Check if the requester is the current owner using the lobby_secret
        if user.socket.state.user_id == lobby.author.author_id and user.socket.state.user_secret == lobby.author.lobby_secret:
            new_owner_id = mes.get("new_owner_id")
            if new_owner_id in lobby.users:
                # Assuming transfer_ownership handles the update of lobby.author
                lobby.transfer_ownership(new_owner_id, lobby.users[new_owner_id].user_secret)
                await broadcast_lobby_sync(lobby)

"""
Websocket protocol:
    in | out, type= "player_chat" | "lobby_chat"
    body= Any
    stamp= float
    user_name= str
    user_id= str

    in | out, type= "test_ping"
    body= Any

    out, type= "lobby_deleted"
    body= str, final message

    out, type= "owner_changed"
    old_owner_id= str
    new_owner_id= str

    out, type= "owner_promoted"
    new_secret= str

    out, type= "lobby_sync"
    users= list of {user_id, user_name, status, join_time}
    author_id= str
    lobby_name= str
    theme= str
    description= str
    
    in, type= "update_lobby_settings"
    lobby_name= str (optional)
    theme= str (optional)
    description= str (optional)
    password= str (optional)

    out, type= "user_joined"
    user_id= str
    user_name= str
    join_time= float

    out, type= "user_left"
    user_id= str
    user_name= str
"""

