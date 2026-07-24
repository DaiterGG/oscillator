from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Response, Request
import random, string
import uuid

from .router.api_router import router

app = FastAPI()
app.include_router(router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mount("/", StaticFiles(directory="./../public_test", html=True), name="index")
    yield

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print("middleware triggered")

    cookie_id = request.cookies.get("user_id")
    cookie_secret = request.cookies.get("user_secret")
    set = False
    if not cookie_id or not cookie_secret:
        print("adding cookie")
        set = True
        cookie_id = str(uuid.uuid4())
        cookie_secret = str(uuid.uuid4())

    request.state.user_id = cookie_id
    request.state.user_secret = cookie_secret

    response: Response = await call_next(request)

    if set:
        response.set_cookie(key="user_id", value=cookie_id, httponly=True, secure=False)
        response.set_cookie(key="user_secret", value=cookie_secret, httponly=True, secure=False)
    return response

def rnd_str(n: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

