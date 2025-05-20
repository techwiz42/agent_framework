import os
import asyncio
import logging
import traceback
import json
from uuid import UUID
from fastapi import FastAPI, Request, APIRouter
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.db.session import db_manager
from app.core.websocket_queue import initialize_connection_health, connection_health
from app.core.config import settings
from app.services.rag.storage_service import rag_storage_service
from app.api import anonymous_websocket

# Load environment variables from .env files
load_dotenv()  # First try default .env file
if os.path.exists('/home/peter/agent_framework/backend/.env'):
    load_dotenv('/home/peter/agent_framework/backend/.env')
if os.path.exists('/etc/cyberiad/.env'):
    load_dotenv('/etc/cyberiad/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    try:
        # Initialize database
        await db_manager.init_db()
        
        # Initialize RAG storage
        try:
            # Create RAG storage directory if it doesn't exist
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            logger.info(f"RAG storage directory initialized: {settings.CHROMA_PERSIST_DIR}")
            
            # Verify RAG storage service is working
            await rag_storage_service.cleanup()  # This will initialize the service
            logger.info("RAG storage service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG storage: {e}")
            logger.error(traceback.format_exc())
            # Continue startup even if RAG fails - we can still operate without it
        
        logger.info("Application startup complete")
        
        yield
        
        # Shutdown logic
        try:
            await rag_storage_service.cleanup()
            logger.info("RAG storage service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up RAG storage: {e}")
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Lifespan event error: {str(e)}")
        raise

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Add a test router directly in main.py to verify routing works
test_router = APIRouter(prefix="/api/debug", tags=["debug"])

@test_router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Debug endpoint working"}

@test_router.get("/routes")
async def list_routes():
    """List all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path if hasattr(route, "path") else "unknown",
            "name": route.name if hasattr(route, "name") else "unknown",
            "methods": list(route.methods) if hasattr(route, "methods") else []
        })
    return {"routes": routes}

app.include_router(test_router)

def register_routers(app: FastAPI):
    """Register all API routers lazily to prevent import issues."""
    logger.info("Registering routers...")
    
    # First register oauth router to ensure it takes precedence
    from app.api.oauth import router as oauth_router
    app.include_router(oauth_router)
    logger.info("OAuth router registered")
    
    # Register standard API routers
    from app.api.auth import router as auth_router
    from app.api.conversations import router as conversations_router
    from app.api.users import router as users_router
    from app.api.messages import router as messages_router
    from app.api.billing import router as billing_router
    from app.api.health import health_router
    from app.api.rag import router as rag_router
    from app.api.agents import router as agents_router
    from app.api.admin import router as admin_router
    from app.api.documents import router as documents_router
    from app.api.email_routes import router as email_router
    from app.api import websockets
    
    # Register Google and OneDrive routers with proper prefixes
    from app.api.google_router import router as google_router
    from app.api.onedrive_router import router as onedrive_router
    
    # Register voice API routers
    from app.api.voice import stt_router
    
    # Log route information
    logger.info(f"Google router prefix: {google_router.prefix}")
    for route in google_router.routes:
        logger.info(f"Google route: {route.path} [{','.join(route.methods)}]")
    
    app.include_router(auth_router)
    app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
    app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
    app.include_router(billing_router)
    app.include_router(websockets.router)
    app.include_router(users_router)
    app.include_router(health_router, prefix="/api")
    app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
    app.include_router(agents_router, prefix="/api", tags=["agents"])
    app.include_router(email_router, prefix="/api")
    app.include_router(admin_router)
    
    # The key part - explicitly include google router with the right prefix
    # Since the google_router already has a prefix of '/google', we need to add '/api'
    app.include_router(google_router, prefix="/api")
    logger.info("Google router registered with prefix /api")
    
    app.include_router(onedrive_router, prefix="/api")
    logger.info("OneDrive router registered with prefix /api")
    
    app.include_router(documents_router, prefix="/api", tags=["documents"])
    
    # Voice API routes
    app.include_router(stt_router, prefix="/api/voice", tags=["voice"])
    logger.info("Voice API router registered with prefix /api/voice")
    
    # Anonymous chat functionality 
    app.include_router(anonymous_websocket.router, prefix="/ws")
    logger.info("Anonymous WebSocket router registered with prefix /ws")
    logger.info("Routes will be available at /ws/anonymous/{agent_type}")
    
    # Mount static files directory for test pages
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Add test routes for speech recognition
    @app.get("/test/microphone")
    async def test_microphone():
        return FileResponse("static/test_microphone.html")
    
    # Log all routes
    logger.info("All routes registered. Registered routes:")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ",".join(route.methods) if route.methods else "unknown"
            logger.info(f"Route: {route.path} [{methods}]")

register_routers(app)

# Redis is not used in this application

@app.on_event("startup")
async def startup_event():
    await initialize_connection_health()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + [
        "http://localhost:3000",     # Local development
        "https://cyberiad.ai",       # Production domain
        "https://*.cyberiad.ai",     # Subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    logger.info(f"Request: {request.method} {path}")
    
    try:
        body = await request.body()
        # Only try to decode if the content-type is text-based
        content_type = request.headers.get("content-type", "")
        if content_type and ("json" in content_type or "text" in content_type or "form" in content_type):
            try:
                body_text = body.decode('utf-8')
                if body_text:
                    print(f"Body: {body_text}")
            except UnicodeDecodeError:
                # This is likely binary data (audio file, etc.)
                print(f"Binary data received: {len(body)} bytes")
        else:
            # This is likely binary data (audio file, etc.)
            print(f"Binary data received: {len(body)} bytes")
    except Exception as e:
        print(f"Could not read body: {e}")

    response = await call_next(request)
    logger.info(f"Response: {request.method} {path} - {response.status_code}")
    return response

# Ensure WebSocket routes have proper CORS handling
@app.middleware("http")
async def add_cors_headers_for_websocket(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/ws/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# Handle legacy routes without /api prefix
@app.middleware("http")
async def redirect_legacy_voice_routes(request: Request, call_next):
    # Check if this is a voice endpoint without the /api prefix
    if request.url.path.startswith("/voice/"):
        # Modify the request path to include the /api prefix
        request.scope["path"] = f"/api{request.url.path}"
        logger.info(f"Redirecting legacy voice route to: {request.scope['path']}")
    
    return await call_next(request)

if __name__ == "__main__":
    port = int(settings.API_PORT)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        ws_max_size=16777216,  # 16MB max message size
        ws="auto",  # Auto WebSocket protocol
        limit_concurrency=10000,  # Max concurrent connections
        limit_max_requests=None,  # No limit on total requests
        backlog=2048,
        log_level="debug"
    )
