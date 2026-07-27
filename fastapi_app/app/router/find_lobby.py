from fastapi import Request, APIRouter
from pydantic import BaseModel
from dataclasses import dataclass

from ..model.lobby import Lobby
from ..model.lobbies import lobbies

router = APIRouter()


# @dataclass
# class FindInfo(BaseModel):
#     # [1, 2, ...]
#     lobby_page: int


class LobbyDisplay:
    lobby_name: str
    author_name: str
    lobby_id: str
    user_count: int
    lobby_theme: str
    lobby_description: str
    is_password: bool

    def __init__(self, id: str, l: Lobby):
        self.lobby_name = l.lobby_name
        self.author_name = l.author.author_name
        self.user_count = len(l.users)
        self.lobby_id = id
        self.lobby_theme = l.theme
        self.lobby_description = l.description
        self.is_password = l.is_password_protected()


@router.get("/api/find_lobby")
async def find_lobby(lobby_page: int = 1):
    one_page = 10
    page_start = (lobby_page - 1) * one_page
    page_end = page_start + one_page
    lobby_list = []
    i = 0
    for id, lobby in lobbies.lobbies.items():
        if i >= page_start:
            lobby_list.append(LobbyDisplay(id, lobby))
        if i >= page_end:
            break
        i += 1

    return {"lobbies": lobby_list}
