from uuid import uuid4
from fastapi import Request, APIRouter
from pydantic import BaseModel
from dataclasses import dataclass

from ..model.lobby import Lobby
from ..model.lobbies import lobbies

router = APIRouter()

@dataclass
class NewLobby(BaseModel):
    user_name: str
    lobby_name: str
    lobby_theme: str
    lobby_description: str
    lobby_password: str | None = None

@router.post("/api/create_lobby")
async def create_lobby( info: NewLobby,
                       request: Request):
    uid = request.state.user_id
    l_id = str(uuid4())
    secret = str(uuid4())
    new_l = Lobby(uid, info.user_name,secret, info.lobby_name,info.lobby_theme, info.lobby_description, info.lobby_password)
    lobbies.insert(l_id, new_l)

    return { "lobby_id": l_id, "lobby_secret": secret }
