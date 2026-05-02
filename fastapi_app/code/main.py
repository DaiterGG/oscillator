from typing import Annotated
from fastapi import Cookie, FastAPI, Response, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dataclasses import dataclass
import random, string
import uuid



app = FastAPI()







@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print("middleware triggered")

    cookie_val = request.cookies.get("user_id")
    if not cookie_val:
        print("adding cookie")
        cookie_val = str(uuid.uuid4())
    request.state.user_id = cookie_val

    response: Response = await call_next(request)

    response.set_cookie(key="user_id", value=cookie_val, httponly=True, secure=False)
    return response

app.mount("/", StaticFiles(directory="./../public_test", html=True), name="index")


