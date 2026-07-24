from fastapi import Request, APIRouter
from pydantic import BaseModel
from dataclasses import dataclass

from ..model.lobby import Lobby
from ..model.lobbies import lobbies

router = APIRouter()

@router.get("/api/ping")
async def ping():
    return
