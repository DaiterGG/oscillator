from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Response, Request
import random, string
import uuid

from .router.lobby import router as r

app = FastAPI()
app.include_router(r)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mount("/", StaticFiles(directory="./../public_test", html=True), name="index")
    yield

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

def rnd_str(n: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

