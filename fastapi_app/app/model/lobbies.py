from fastapi import HTTPException
from fastapi.datastructures import State
from .lobby import Lobby

class Lobbies:
    lobbies: dict[str, Lobby]
    def __init__(self) -> None:
        self.lobbies = {}
    def get_or_status(self, key: str, status: int) -> Lobby:
        lobby = self.lobbies.get(key)
        if not lobby:
            raise HTTPException(status_code=status, detail=f"lobby {key} doesn't exist")
        return lobby
    def remove(self, key: str):
        self.lobbies.pop(key)
    def insert(self, key: str, new_lobby: Lobby):
        self.lobbies[key] = new_lobby
    def delete_if_empty(self, key):
        lobby = self.lobbies.get(key)
        if not lobby:
            return
        if len(lobby.users) == 0:
            self.lobbies.pop(key)
    async def disconnect_user(self, lobby_id: str, user_id: str):
        lobby = self.get_or_status(lobby_id, 200)
        await lobby.disconnect_user(user_id)
        self.delete_if_empty(lobby_id)

    async def validate_user(self, lobby_id: str, user_id: str, state: State):
        lobby = self.get_or_status(lobby_id, 200)
        user = lobby.get_user(user_id)
        user.validate_user_state(state)

lobbies = Lobbies()
