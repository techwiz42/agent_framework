from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from typing import List, Optional, Dict, AsyncGenerator, Union
from datetime import datetime
from uuid import UUID, uuid4
from app.core.config import settings
import logging
import os
import traceback
from app.models.domain.models import Base, User, Thread, ThreadParticipant, Message, MessageInfo, ThreadAgent

# Set up logging
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

# Connection pool configuration
POOL_SIZE = 20  # Maximum number of persistent connections
MAX_OVERFLOW = 10  # Maximum number of additional connections
POOL_TIMEOUT = 30  # Seconds to wait for a connection from the pool
POOL_RECYCLE = 1800  # Recycle connections after 30 minutes
POOL_PRE_PING = True  # Enable connection health checks

# Create engine with pool configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=POOL_PRE_PING
)

# Create sessionmaker without pool parameters
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = AsyncSessionLocal
        self._pool_stats = {
            'total_checked_out': 0,
            'total_checked_in': 0,
            'peak_connections': 0,
            'connection_errors': 0
        }

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session from the pool."""
        session = self.SessionLocal()
        try:
            self._pool_stats['total_checked_out'] += 1
            self._pool_stats['peak_connections'] = max(
                self._pool_stats['peak_connections'],
                engine.pool.size() + engine.pool.overflow()
            )
            yield session
        except Exception as e:
            self._pool_stats['connection_errors'] += 1
            logger.error(f"Database session error: {e}")
            raise
        finally:
            self._pool_stats['total_checked_in'] += 1
            await session.close()

    def get_pool_stats(self) -> dict:
        """Get current connection pool statistics."""
        return {
            **self._pool_stats,
            'current_connections': engine.pool.size(),
            'available_connections': engine.pool.size() - engine.pool.checkedout(),
            'overflow_connections': engine.pool.overflow(),
            'checkedout_connections': engine.pool.checkedout()
        }

    async def init_db(self):
        """Initialize database with connection pooling."""
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def verify_pool_health(self) -> bool:
        """Verify connection pool health."""
        try:
            async with self.SessionLocal() as session:
                await session.execute(select(1))
            return True
        except Exception as e:
            logger.error(f"Pool health check failed: {e}")
            return False

    async def cleanup_pool(self):
        """Cleanup and dispose of the connection pool."""
        try:
            await engine.dispose()
            logger.info("Connection pool disposed successfully")
        except Exception as e:
            logger.error(f"Error disposing connection pool: {e}")
            raise

    # Existing database operation methods with connection pooling...
    async def get_user_by_username(self, session: AsyncSession, username: str):
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_user_by_email(self, session: AsyncSession, email: str):
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_messages(self, session: AsyncSession, thread_id: UUID) -> List[Message]:
        result = await session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .options(joinedload(Message.message_info))  # This eagerly loads the message_info
        )
        return result.scalars().all()

    async def create_user(
        self,
        session: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
        phone: str = None
    ) -> User:
        try:
            user = User(
                username=username,
                email=email,
                phone=phone,
                hashed_password=hashed_password,
                created_at=datetime.utcnow(),
                is_active=True,
                tokens_purchased=50000, 
                tokens_consumed=0
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    async def create_thread(
        self,
        session: AsyncSession,
        owner_id: UUID,
        title: str,
        description: Optional[str] = None
    ):
        thread = Thread(
            id=uuid4(),
            owner_id=owner_id,
            title=title,
            description=description,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            settings={}
        )
        session.add(thread)
        return thread

    async def get_thread(self, session: AsyncSession, thread_id: UUID):
        result = await session.execute(
            select(Thread)
            .where(Thread.id == thread_id)
            .options(joinedload(Thread.participants))
        )
        return result.scalars().first()

    async def get_thread_agents(self, session: AsyncSession, thread_id: UUID):
            result = await session.execute(
                select(ThreadAgent)
                .where(ThreadAgent.thread_id == thread_id)
                .where(ThreadAgent.is_active == True)
            )
            return result.scalars().all()

    async def get_user_threads(self, session: AsyncSession, user_id: UUID):
        try:
            result = await session.execute(
                select(Thread)
                .outerjoin(ThreadParticipant)
                .outerjoin(ThreadAgent)
                .where(Thread.owner_id == user_id)
                .options(
                    joinedload(Thread.participants),
                    joinedload(Thread.agents)
                )
                .order_by(desc(Thread.updated_at))
            )
            return result.scalars().unique().all()
        except Exception as e:
            logger.error(f"Error getting user threads: {e}")
            raise

    async def add_thread_participant(
        self,
        session: AsyncSession,
        thread_id: UUID,
        email: str,
        name: str
    ) -> ThreadParticipant:
        participant = ThreadParticipant(
            id=uuid4(),
            thread_id=thread_id,
            email=email,
            name=name,
            joined_at=datetime.utcnow(),
            is_active=True
        )
        session.add(participant)
        return participant

    async def add_agent_to_thread(
        self,
        session: AsyncSession,
        thread_id: UUID,
        agent_type: str
    ) -> ThreadAgent:
        agent = ThreadAgent(
            id=uuid4(),
            thread_id=thread_id,
            agent_type=agent_type.upper(),
            is_active=True,
            settings={},
            created_at=datetime.utcnow()
        )
        session.add(agent)
        return agent

    async def is_thread_participant(
        self,
        session: AsyncSession,
        thread_id: UUID,
        identifier: Union[UUID, str]
    ) -> bool:
        try:
            if isinstance(identifier, UUID):
                user = await session.get(User, identifier)
                if not user:
                    return False
                email = user.email
            else:
                email = identifier

            result = await session.execute(
                select(ThreadParticipant)
                .where(and_(
                    ThreadParticipant.thread_id == thread_id,
                    ThreadParticipant.email == email,
                    ThreadParticipant.is_active == True
                ))
            )
            return result.scalars().first() is not None

        except Exception as e:
            logger.error(f"Error checking thread participation: {e}")
            return False

    async def create_message_info(
        self,
        session: AsyncSession,
        message_id: UUID,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        programming_language: Optional[str] = None,
        file_id: Optional[str] = None,
        chunk_count: Optional[int] = None,
        source: Optional[str] = None,
        participant_name: Optional[str] = None,
        participant_email: Optional[str] = None,
        is_owner: Optional[bool] = None,
        tokens_used: Optional[int] = None
    ) -> MessageInfo:
        message_info = MessageInfo(
            message_id=message_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            programming_language=programming_language,
            file_id=file_id,
            chunk_count=chunk_count,
            source=source,
            participant_name=participant_name,
            participant_email=participant_email,
            is_owner=is_owner,
            tokens_used=tokens_used
        )
        session.add(message_info)
        return message_info

    async def get_message_info(
        self,
        session: AsyncSession,
        message_id: UUID
    ) -> Optional[MessageInfo]:
        result = await session.execute(
            select(MessageInfo).where(MessageInfo.message_id == message_id)
        )
        return result.scalars().first()

# Create database manager instance
db_manager = DatabaseManager()
