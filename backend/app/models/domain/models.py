import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from datetime import datetime
import uuid
import enum
from typing import Optional, List
import os

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

class ThreadStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole, name='user_role'), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, unique=True, nullable=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    tokens_purchased = Column(Integer, default=0)
    tokens_consumed = Column(Integer, default=0)
    stripe_customer_id = Column(String, unique=True, nullable=True)

    @property
    def tokens_remaining(self):
        purchased = 0
        consumed = 0
        if self.tokens_purchased is not None:
            purchased = self.tokens_purchased
        if self.tokens_consumed is not None:
            consumed = self.tokens_consumed
        return purchased - consumed

    # Relationships
    owned_threads = relationship("Thread", back_populates="owner")
    read_receipts = relationship("MessageReadReceipt", back_populates="user")

class Thread(Base):
    __tablename__ = "threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ThreadStatus), default=ThreadStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    
    # Thread is primarily a collection of messages
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    
    # Supporting relationships
    owner = relationship("User", back_populates="owned_threads")
    participants = relationship("ThreadParticipant", back_populates="thread", cascade="all, delete-orphan")
    agents = relationship("ThreadAgent", back_populates="thread", cascade="all, delete-orphan") 

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("thread_participants.id"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("thread_agents.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)

    # Message organization
    thread = relationship("Thread", back_populates="messages")
    participant = relationship("ThreadParticipant", back_populates="messages")
    agent = relationship("ThreadAgent", back_populates="messages")
    parent = relationship("Message", remote_side=[id], backref="replies")
    read_receipts = relationship("MessageReadReceipt", back_populates="message")
    message_info = relationship("MessageInfo",
                                back_populates="message", 
                                cascade="all, delete-orphan",
                                uselist=False)
    # Ensure message is from either a participant or an agent, not both
    __table_args__ = (
        sa.CheckConstraint(
            '(CASE WHEN participant_id IS NOT NULL THEN 1 ELSE 0 END) + '
            '(CASE WHEN agent_id IS NOT NULL THEN 1 ELSE 0 END) = 1',
            name='one_sender_type'
        ),
    )

class MessageInfo(Base):
    __tablename__ = "message_info"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    file_name = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    programming_language = Column(String)
    file_id = Column(String)
    chunk_count = Column(Integer)
    source = Column(String)
    participant_name = Column(String)
    participant_email = Column(String)
    is_owner = Column(Boolean)
    tokens_used = Column(Integer)

    message = relationship("Message", back_populates="message_info")
    
    # Add index for faster lookups
    __table_args__ = (
        sa.Index('idx_message_info_message_id', 'message_id'),
    )

class ThreadParticipant(Base):
    __tablename__ = "thread_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # New columns for invitation tracking
    invitation_token = Column(String, nullable=True)
    invitation_sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    thread = relationship("Thread", back_populates="participants")
    messages = relationship("Message", back_populates="participant")

    # Email must be unique within a thread
    __table_args__ = (
        sa.UniqueConstraint('thread_id', 'email', name='unique_email_per_thread'),
    )

class ThreadAgent(Base):
    __tablename__ = "thread_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    agent_type = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thread = relationship("Thread", back_populates="agents")
    messages = relationship("Message", back_populates="agent")

    # Only one agent of each type per thread
    __table_args__ = (
        sa.UniqueConstraint('thread_id', 'agent_type', name='unique_agent_type_per_thread'),
    )

class MessageReadReceipt(Base):
    __tablename__ = "message_read_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(DateTime, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="read_receipts")
    user = relationship("User", back_populates="read_receipts")