from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api.websockets import router as websocket_router

api_router = APIRouter()

# Include API endpoints
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websockets"])