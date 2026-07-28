import time
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..model.lobbies import lobbies
from ..model.lobby import Lobby
from ..model.connected_user import ConnectedUser

router = APIRouter()

async def broadcast_lobby_sync(lobby: Lobby):
    user_list = []
    for uid, u in lobby.users.items():
        # Include all users, even disconnected ones, so they show up in the lobby list
        user_list.append({
            "user_id": uid,
            "user_name": u.user_name,
            "status": u.status,
            "join_time": u.join_time
        })
    
    for _, user in lobby.users.items():
        if user.status == "connected":
            data = {
                "type": "lobby_sync",
                "users": user_list,
                "author_id": lobby.author.author_id,
                "lobby_name": lobby.lobby_name,
                "theme": lobby.theme,
                "description": lobby.description
            }
            # Only send password to the owner
            if user.socket.cookies.get("user_id") == lobby.author.author_id:
                data["password"] = lobby.password
            
            await user.socket.send_json(data)

@router.websocket("/api/join_lobby")
async def join_lobby(ws: WebSocket):
    try:
        await join(ws)
    except Exception:
        traceback.print_exc()
    finally:
        lobby_id = ws.query_params["lobby_id"]
        if lobby_id:
            lobbies.delete_if_empty(lobby_id)


async def join(ws: WebSocket):
    await ws.accept()
    
    # 1. Initial Handshake: Get user/lobby info from query params
    try:
        user_name = ws.query_params["user_name"]
        lobby_id = ws.query_params["lobby_id"]
        # Fallback to query params for testing if not in cookies
        u_id = ws.cookies.get("user_id") or ws.query_params.get("user_id")
        u_secret = ws.cookies.get("user_secret") or ws.query_params.get("user_secret")
        
        if not u_id or not u_secret:
             # If not provided in cookies OR query params, fail
             raise Exception("Missing credentials")
             
    except Exception:
        await ws.close(code=4000, reason="Missing credentials")
        return

    # Verify Lobby
    lobby = lobbies.lobbies.get(lobby_id)
    if not lobby:
        await ws.close(code=4004, reason="Lobby not found")
        return
        
    author_user = lobby.users.get(lobby.author.author_id)
    # If author is disconnected, deny everyone except the author
    if author_user and author_user.status == "disconnected" and u_id != lobby.author.author_id:
        await ws.close(code=4004, reason="Lobby not found")
        return

    # 2. Challenge Phase (if protected and user is not author)
    if lobby.is_password_protected() and u_id != lobby.author.author_id:
        while True:
            await ws.send_json({"type": "challenge", "reason": "password_required"})
            
            # Wait for password submission
            try:
                resp = await ws.receive_json()
                if resp.get("type") == "password_submit":
                    password = resp.get("password")
                else:
                    await ws.close(code=4003, reason="Expected password_submit")
                    return
            except Exception:
                await ws.close(code=4000, reason="Handshake failed")
                return

            # Validate password
            if lobby.password == password:
                break # Correct password
            else:
                await ws.send_json({"type": "auth_error", "message": "Wrong password"})
                # Loop continues for retry

    # Handle reconnection or new join
    if u_id in lobby.users:
        user = lobby.users[u_id]
        if user.status == "disconnected":
            if user.reconnect_task: user.reconnect_task.cancel()
            user.status = "connected"
            user.socket = ws
            # Send sync and chat history to the reconnected user
            await broadcast_lobby_sync(lobby)
            await ws.send_json({"type": "player_chat_history", "messages": lobby.player_history})
            await ws.send_json({"type": "lobby_chat_history", "messages": lobby.lobby_history})
        else:
            await ws.close(code=4009, reason="already connected")
            return
    else:
        user = ConnectedUser(user_name=user_name, lobby_id=lobby_id, socket=ws)
        lobby.users[u_id] = user
        await broadcast_lobby_sync(lobby)
        await ws.send_json({"type": "player_chat_history", "messages": lobby.player_history})
        await ws.send_json({"type": "lobby_chat_history", "messages": lobby.lobby_history})
        for other_id, other_user in lobby.users.items():
            if other_id != u_id:
                try: 
                    await other_user.socket.send_json({"type": "user_joined", "user_id": u_id, "user_name": user_name, "join_time": user.join_time})
                except:
                    pass

    try:
        while True:
            await websocket_read_message(user)
    except WebSocketDisconnect:
        pass
    finally:
        user.status = "disconnected"
        await broadcast_lobby_sync(lobby)
        
        # Wait 3 seconds and remove if still disconnected
        await asyncio.sleep(3)
        if user.status == "disconnected":
            if u_id in lobby.users:
                # If the owner leaves, transfer ownership
                if u_id == lobby.author.author_id:
                    new_owner = lobby.get_new_owner()
                    if new_owner:
                        new_owner_id, new_owner_user, new_secret = new_owner
                        lobby.transfer_ownership(new_owner_id, new_secret)
                        # Notify the new owner of the new secret
                        await new_owner_user.socket.send_json({"type": "owner_promoted", "new_secret": new_secret})
                        await broadcast_lobby_sync(lobby)

                del lobby.users[u_id]
                await broadcast_lobby_sync(lobby)
                
                # Notify other users only when the user is actually removed
                for other_id, other_user in lobby.users.items():
                    if other_id != u_id and other_user.status == "connected":
                        try:
                            await other_user.socket.send_json({"type": "user_left", "user_id": u_id, "user_name": user.user_name})
                        except:
                            pass

async def websocket_read_message(user: ConnectedUser):
    mes = await user.socket.receive_json()
    # Fallback to query params for testing if not in cookies
    user_id = user.socket.cookies.get("user_id") or user.socket.query_params.get("user_id")
    user_secret = user.socket.cookies.get("user_secret") or user.socket.query_params.get("user_secret")
    print("read message")
    if mes["type"] in ["player_chat", "lobby_chat"]:
        mes["stamp"] = str(time.time())
        mes["user_name"] = user.user_name
        mes["user_id"] = user_id

        lobby = lobbies.lobbies.get(user.lobby_id)
        if not lobby:
            await user.socket.close(code=4004, reason="lobby not found")
            return
        
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
        lobby = lobbies.lobbies.get(user.lobby_id)
        if not lobby:
            await user.socket.close(code=4004, reason="lobby not found")
            return
        
        # Correct check: requester must be author AND provide the correct lobby_secret
        provided_secret = mes.get("lobby_secret") 
        
        if user_id == lobby.author.author_id and provided_secret == lobby.author.lobby_secret:
            if "lobby_name" in mes:
                lobby.lobby_name = mes["lobby_name"] if mes["lobby_name"].strip() else "None"
            if "theme" in mes:
                lobby.theme = mes["theme"] if mes["theme"].strip() else "None"
            if "description" in mes:
                lobby.description = mes["description"] if mes["description"].strip() else "None"
            if "password" in mes:
                new_password = mes["password"]
                lobby.password = new_password if new_password and new_password.strip() else None
            
            await broadcast_lobby_sync(lobby)

    elif mes["type"] == "set_owner":
        lobby = lobbies.lobbies.get(user.lobby_id)
        if not lobby:
            await user.socket.close(code=4004, reason="lobby not found")
            return
        
        # Correct check: requester must be author AND provide the correct lobby_secret
        provided_secret = mes.get("lobby_secret")

        if user_id == lobby.author.author_id and provided_secret == lobby.author.lobby_secret:
            new_owner_id = mes.get("new_owner_id")
            if new_owner_id in lobby.users:
                import uuid
                new_lobby_secret = str(uuid.uuid4())
                lobby.transfer_ownership(new_owner_id, new_lobby_secret)
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

