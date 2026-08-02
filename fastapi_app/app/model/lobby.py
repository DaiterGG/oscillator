from typing import Self
from uuid import uuid4
from fastapi import HTTPException
from fastapi.websockets import WebSocketState
from dataclasses import dataclass, field
from enum import Enum

from .connected_user import ConnectedUser

class PlayerControllsAccess(str, Enum):
    AUTHOR_ONLY = "author_only"
    ALL = "all"
    WHITELIST = "whitelist"

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
    theme: str
    description: str
    password: str | None
    users: dict[str, 'ConnectedUser']
    player_history: list[dict]
    current_track_index: int
    # start_time: float
    is_shuffled: bool
    # is_looped: bool
    # is_paused: bool
    player_controlls_access: PlayerControllsAccess
    whitelist: list[str]
    chat_history: list[dict]
    ready_users: set[str] = field(default_factory=set)

    def __init__(self, user_id: str, user_name: str, lobby_secret: str, lobby_name: str,theme: str, description: str, password: str | None):
        self.author = LobbyOwnership(user_id, user_name, lobby_secret)
        self.lobby_name = lobby_name
        self.users = {}
        self.player_history = []
        self.current_track_index = -1
        self.is_shuffled = False
        # self.start_time = 0.0
        # self.is_looped = False
        # self.is_paused = True
        self.player_controlls_access = PlayerControllsAccess.ALL
        self.whitelist = []
        self.chat_history = []
        self.description = description
        self.theme = theme
        self.password = password
        self.ready_users = set()
    def is_password_protected(self) -> bool:
        return self.password is not '' and self.password is not None

    def get_user(self, key: str) -> 'ConnectedUser':
        user = self.users.get(key)
        if not user:
            raise HTTPException(status_code=400, detail=f"user {key} doesn't exist")
        return user

    def get_new_owner(self) -> tuple[str, ConnectedUser, str] | None:
        # returns (new_owner_id, new_owner_connected_user, new_secret)
        if len(self.users) <= 1:
            return None
        
        # Iterate backwards to find the "latest" user who is not the author
        for u_id in reversed(list(self.users.keys())):
            if u_id != self.author.author_id:
                new_secret = str(uuid4())
                return u_id, self.users[u_id], new_secret
        return None

    def transfer_ownership(self, new_owner_id: str, new_secret: str):
        user = self.users[new_owner_id]
        self.author = LobbyOwnership(new_owner_id, user.user_name, new_secret)

    async def disconnect_user(self, key: str):
        user = self.users.get(key)

        if not user:
            raise HTTPException(status_code=400, detail=f"user {key} doesn't exist")

        user = self.users.pop(key)

        # print(user.socket.application_state)
        # if user.socket.application_state != WebSocketState.DISCONNECTED:
        #     await user.socket.close()
