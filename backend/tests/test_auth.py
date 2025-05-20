import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime
from uuid import uuid4
from typing import AsyncGenerator, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.domain.models import Base, User, Thread, ThreadParticipant
from app.core.security import security_manager
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/cyberiad_test"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture
async def test_app():
    """Create a test FastAPI app with test database configuration."""
    def get_test_db():
        async def get_db() -> AsyncGenerator[AsyncSession, None]:
            async with TestingSessionLocal() as session:
                yield session
        return get_db

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
    
    # Configure CORS for test app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Override the database dependency
    from app.db.session import db_manager
    app.dependency_overrides[db_manager.get_session] = get_test_db()

    return app

@pytest.fixture(scope="session")
async def create_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest.fixture(scope="function", autouse=True)
async def reset_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user with proper credentials."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

    user = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=security_manager.get_password_hash(user_data["password"]),
        email_verified=True,
        tokens_purchased=50000,
        tokens_consumed=0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {"user": user, "credentials": user_data}

@pytest.fixture
async def authenticated_client(async_client: AsyncClient, test_user: Dict) -> AsyncClient:
    """Get an authenticated client."""
    response = await async_client.post(
        "/api/auth/token",
        data={
            "username": test_user["credentials"]["username"],
            "password": test_user["credentials"]["password"],
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    data = response.json()
    async_client.headers["Authorization"] = f"Bearer {data['access_token']}"
    return async_client

@pytest.fixture
async def test_conversation(db_session: AsyncSession, test_user: Dict) -> Dict:
    """Create a test conversation."""
    thread = Thread(
        id=uuid4(),
        owner_id=test_user["user"].id,
        title="Test Thread",
        created_at=datetime.utcnow(),
        status='ACTIVE'
    )
    db_session.add(thread)

    participant_email = "participant@example.com"
    participant = ThreadParticipant(
        id=uuid4(),
        thread_id=thread.id,
        email=participant_email,
        name="Test Participant",
        joined_at=datetime.utcnow(),
        is_active=True
    )
    db_session.add(participant)
    await db_session.commit()
    await db_session.refresh(thread)
    await db_session.refresh(participant)

    return {
        "thread": thread,
        "participant": participant
    }

# Test cases
async def test_user_registration(async_client: AsyncClient, db_session: AsyncSession):
    """Test user registration with unique username."""
    unique_username = f"newuser_{uuid4().hex[:8]}"
    response = await async_client.post(
        "/api/auth/register",
        json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "email" in data
    assert "pending" in data["message"].lower()  # Verify it mentions registration is pending
    assert unique_username in data["email"]  # Verify the email matches what we sent
    
async def test_user_registration_duplicate_email(async_client: AsyncClient, test_user: Dict):
    """Test user registration with an email that already exists."""
    response = await async_client.post(
        "/api/auth/register",
        json={
            "username": "different_username",
            "email": test_user["credentials"]["email"],  # Using existing email
            "password": "securepass123"
        }
    )
    # Should still return 200 status but with a helpful message
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "email" in data
    assert "already registered" in data["message"].lower()  # Verify it mentions email is already registered

async def test_user_login(async_client: AsyncClient, test_user: Dict):
    """Test user login."""
    response = await async_client.post(
        "/api/auth/token",
        data={
            "username": test_user["credentials"]["username"],
            "password": test_user["credentials"]["password"],
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

async def test_invalid_login(async_client: AsyncClient):
    """Test invalid login."""
    response = await async_client.post(
        "/api/auth/token",
        data={
            "username": "wronguser",
            "password": "wrongpass",
            "grant_type": "password"
        }
    )
    assert response.status_code == 401

async def test_participant_invitation(
    authenticated_client: AsyncClient,
    test_conversation: Dict
):
    """Test participant invitation."""
    thread = test_conversation["thread"]
    new_participant = {
        "email": f"new_participant_{uuid4().hex[:8]}@example.com",
        "name": "New Test Participant"
    }
    
    response = await authenticated_client.post(
        f"/api/conversations/{thread.id}/add-participant",
        json=new_participant
    )
    assert response.status_code == 200
    assert "message" in response.json()

async def test_participant_join(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_conversation: Dict
):
    """Test participant joining."""
    thread = test_conversation["thread"]
    participant = test_conversation["participant"]

    # Create and store invitation token
    invitation_token = security_manager.create_invitation_token({
        "thread_id": str(thread.id),
        "email": participant.email
    })

    # Update participant with invitation token
    participant.invitation_token = invitation_token
    participant.invitation_sent_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(participant)

    # Verify token in database
    result = await db_session.execute(
        select(ThreadParticipant).where(ThreadParticipant.id == participant.id)
    )
    stored_participant = result.scalar_one_or_none()
    assert stored_participant is not None
    assert stored_participant.invitation_token == invitation_token

    # Test joining with invitation
    response = await async_client.post(
        "/api/conversations/join",
        json={
            "invitation_token": invitation_token,
            "name": "Updated Participant Name"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "participant_token" in data
    assert data["email"] == participant.email
