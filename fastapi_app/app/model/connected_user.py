from dataclasses import dataclass
import dataclasses
import time
from fastapi import HTTPException, WebSocket
from fastapi.datastructures import State
from typing import Optional
import asyncio

@dataclass
class ConnectedUser:
    """ data maintained while connection is open """
    user_name: str
    lobby_id: str
    socket: WebSocket
    status: str = "connected"
    reconnect_task: Optional[asyncio.Task] = None
    join_time: float = dataclasses.field(default_factory=time.time)

    def validate_user_state(self, state: State):
        server_side = self.socket.cookies["user_secret"]
        client_side = state.user_secret
        if not client_side:
            raise HTTPException(status_code=422, detail=f"cookie was not found")
        if server_side != client_side:
            raise HTTPException(status_code=422, detail="wrong secret")
