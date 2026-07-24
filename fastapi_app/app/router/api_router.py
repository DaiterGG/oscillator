from fastapi import APIRouter
from .create_lobby import router as create_lobby_router
from .delete_lobby import router as delete_lobby_router
from .websocket import router as websocket_router
from .find_lobby import router as find_lobby_router
from .ping import router as ping_router
from .leave_lobby import router as leave_lobby_router

router = APIRouter()

router.include_router(create_lobby_router, tags=["lobby"])
router.include_router(delete_lobby_router, tags=["lobby"])
router.include_router(websocket_router, tags=["websocket"])
router.include_router(find_lobby_router, tags=["list"])
router.include_router(ping_router, tags=["ping"])
router.include_router(leave_lobby_router, tags=["lobby"])
