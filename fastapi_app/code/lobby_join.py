from dataclasses import dataclass
import time
from fastapi import WebSocket,  WebSocketDisconnect

from lobby_create import Lobbies
from main import app

@dataclass
class ConnectedUser:
    """
        datatype maintained while connection is open
    """
    user_id: str
    user_name: str
    lobby_id: str
    socket: WebSocket


@app.websocket("/api/connect/")
async def connect_to_lobby(ws: WebSocket):
    connected_user = await join_lobby(ws)
    if not connected_user:
        return

        
    try:
        while True:
            await websocket_read_message(connected_user)
    except WebSocketDisconnect:
        print("Client disconnected normally, no error")
    finally:
        await ws.close()

async def join_lobby(ws: WebSocket) -> ConnectedUser | None:
    try:
        user_name = ws.query_params["user_name"]
        print(f"user {user_name} connecting")
        lobby_id = ws.query_params["lobby_id"]
        print(f"to lobby {lobby_id}")
        u_id = ws.cookies["user_id"]
    except:
        print("credentials was not provided")
        await ws.close()
        return

    await ws.accept()
    
    connected = ConnectedUser(user_id=u_id,user_name=user_name,lobby_id=lobby_id,socket=ws)
    Lobbies[lobby_id].users.append(connected)
    return connected

async def websocket_read_message(user: ConnectedUser):
    mes = await user.socket.receive_json()
    if mes["type"] == "message":
        mes["stamp"] = str(time.time())
        lobby = Lobbies[user.lobby_id]
        for other_user in lobby.users:
            if other_user.user_id == user.user_id:
                continue
            await user.socket.send_json(mes)

    elif mes["type"] == "test_ping":
        await user.socket.send_json(mes)

