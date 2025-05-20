# tests/conftest.py
import datetime
from datetime import timezone
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import logging
import sys
import os
from pathlib import Path

# Configure logging - reduce noise during tests
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('passlib').setLevel(logging.WARNING)

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import Base
from app.models.domain.models import User, Thread
from main import app, lifespan
from app.core.websocket_queue import connection_health as connection_manager
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI

# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop scoped to the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create and configure test database engine."""
    try:
        # Create engine with pooling disabled for tests
        engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=NullPool,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True  # Enable connection health checks
        )

        # Verify database connection and setup schema
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))

            # Drop and recreate schema with all tables
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(Base.metadata.create_all)

        # Log the type of the engine object
        logging.info(f"Yielding test engine of type: {type(engine)}")
        assert hasattr(engine, "begin"), "Engine object does not support the required async methods."

        yield engine

    except Exception as e:
        pytest.fail(f"Failed to setup test database: {str(e)}")

    finally:
        try:
            await engine.dispose()
        except Exception as e:
            logging.error(f"Error disposing test engine: {e}")


