from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from dataclasses import dataclass

from ..model.lobbies import lobbies

router = APIRouter()

@dataclass
class DeleteLobbyInfo(BaseModel):
    lobby_id: str
    lobby_secret: str
    final_message: str

@router.post("/api/delete_lobby")
async def delete_lobby(info: DeleteLobbyInfo):
    lobby = lobbies.get_or_status(info.lobby_id, 400)
    if lobby.author.lobby_secret != info.lobby_secret:
        raise HTTPException(status_code=401, detail="lobby has a different secret")

    for _, user in lobby.users.items():
        # TODO: join set?
        await user.socket.send_json({"type": "lobby_deleted", "body": info.final_message })
        await user.socket.close()

    lobbies.remove(info.lobby_id)
    return
