from fastapi import HTTPException, WebSocket, WebSocketDisconnect, Request, APIRouter
from pydantic import BaseModel
from dataclasses import dataclass

import time, random, string

router = APIRouter()

@dataclass
class LobbyOwnership:
    """
    mutable author info
    Attributes:
        lobby_secret: secret to manage lobby, mutable on owner change
    """
    author_id: str
    author_name: str
    lobby_secret: str

@dataclass
class Lobby:
    author: LobbyOwnership
    lobby_name: str
    users: list['ConnectedUser']

Lobbies: dict[str, Lobby] = {}

@dataclass
class NewLobby(BaseModel):
    user_name: str
    lobby_name: str

@dataclass
class NewLobbyResponse(BaseModel):
    lobby_id: str

@router.post("/api/create_lobby")
async def create_lobby( info: NewLobby,
                       request: Request):
    uid = request.state.user_id
    l_id = rnd_str(20)
    secret = rnd_str(20)
    owner =  LobbyOwnership(uid, info.lobby_name, secret)
    new_l = Lobby(owner, info.lobby_name,[])
    Lobbies[l_id] = new_l

    return { "lobby_id": l_id, "lobby_secret": secret }

def rnd_str(n: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

@dataclass
class DeleteLobbyInfo(BaseModel):
    lobby_id: str
    lobby_secret: str
    final_message: str

@router.post("/api/delete_lobby")
async def delete_lobby(info: DeleteLobbyInfo):
    lobby = Lobbies.get(info.lobby_id, None)
    if not lobby:
        raise HTTPException(status_code=400, detail="lobby is not found")
    if lobby.author.lobby_secret != info.lobby_secret:
        raise HTTPException(status_code=401, detail="lobby has a different secret")

    for user in lobby.users:
        # TODO: join set?
        await user.socket.send_json({"type": "lobby_deleted", "body": info.final_message })
        await user.socket.close()

    Lobbies.pop(info.lobby_id)
    return



@dataclass
class ConnectedUser:
    """ data maintained while connection is open """
    user_id: str
    user_name: str
    lobby_id: str
    socket: WebSocket


@router.websocket("/api/join_lobby")
async def join_lobby(ws: WebSocket):
    connected_user = await parse_and_connect(ws)
    try:
        await websocket_read_message(connected_user)
    except WebSocketDisconnect:
        print("Client disconnected normally, no error")
    finally:
        await ws.close()

async def parse_and_connect(ws: WebSocket) -> ConnectedUser:
    print("connecting")
    try:
        user_name = ws.query_params["user_name"]
        print(f"user {user_name} connecting")
        lobby_id = ws.query_params["lobby_id"]
        print(f"to lobby {lobby_id}")
        u_id = ws.cookies["user_id"]
    except:
        await ws.close()
        raise HTTPException(status_code=400, detail="credentials was not provided")

    await ws.accept()
    
    connected = ConnectedUser(user_id=u_id, user_name=user_name, lobby_id=lobby_id, socket=ws)
    lobby = Lobbies.get(lobby_id)
    if not lobby:
        raise HTTPException(status_code=400, detail="lobby doesn't exist")

    lobby.users.append(connected)
    return connected

async def websocket_read_message(user: ConnectedUser):
    async for mes in user.socket.iter_json():
        print("read message")
        if mes["type"] == "message":
            mes["stamp"] = str(time.time())
            lobby = Lobbies[user.lobby_id]
            for other_user in lobby.users:
                if other_user.user_id == user.user_id:
                    continue

                print(f"sending message from {user.user_name} to {other_user.user_name}")
                await other_user.socket.send_json(mes)
                print(f"message sent from {user.user_name} to {other_user.user_name}")

        elif mes["type"] == "test_ping":
            await user.socket.send_json(mes)

"""
Websocket protocol:
    in | out, type= "message"
    out, stamp= float
    body= Any

    in | out, type= "test_ping"
    body= Any

    out, type= "lobby_deleted"
    body= str, final message
"""

