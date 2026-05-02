import random, string

from fastapi import Request 
from pydantic import BaseModel
from dataclasses import dataclass

from lobby_join import ConnectedUser

from main import app


@dataclass
class Lobby:
    author_id: str
    author_name: str
    lobby_name: str
    users: list[ConnectedUser]

Lobbies: dict[str, Lobby] = {}

@dataclass
class NewLobby(BaseModel):
    user_name: str
    lobby_name: str

@dataclass
class NewLobbyResponse(BaseModel):
    lobby_id: str

@app.post("/api/create_lobby/")
async def create_lobby( info: NewLobby,
                       request: Request):
    uid = request.state.user_id
    l_id = rnd_str(20)
    new_l = Lobby(uid, info.user_name, info.lobby_name,[])
    Lobbies[l_id] = new_l

    return { "lobby_id": l_id }


def rnd_str(n: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

