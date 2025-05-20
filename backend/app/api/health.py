from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}

