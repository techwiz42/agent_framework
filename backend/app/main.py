from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os

from app.core.config import settings
from app.api.routes import api_router
from app.services.agents import agent_interface

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.BUFFER_SAVE_DIR, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Agent Framework API",
    description="API for Agent Framework - A multi-user, multi-agent collaborative workspace",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

# Get available agents endpoint
@app.get("/api/agents/available", tags=["agents"])
async def get_available_agents():
    """
    Get a list of all available agent types.
    """
    return agent_interface.get_agent_types()

# Get agent descriptions endpoint
@app.get("/api/agents/descriptions", tags=["agents"])
async def get_agent_descriptions():
    """
    Get descriptions for all available agents.
    """
    return agent_interface.get_agent_descriptions()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Agent Framework API")
    logger.info(f"Available agent types: {agent_interface.get_agent_types()}")
    try:
        # Initialize any startup tasks here
        logger.info("Initialization complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Agent Framework API")
    # Perform any cleanup tasks here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )