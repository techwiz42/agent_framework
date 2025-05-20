from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr

# Auth Schemas
class UserAuth(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    password_confirm: str

class Token(BaseModel):
    access_token: str
    token_type: constr(pattern="^bearer$")
    user_id: str
    username: str
    email: str
    phone: Optional[str] = None

# Participant Schemas
class ParticipantCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class ParticipantInfo(BaseModel):
    """Represents a participant in a conversation"""
    email: EmailStr
    name: Optional[str]
    is_active: bool
    joined_at: datetime
    last_read_at: Optional[datetime]

    @classmethod
    def from_thread_participant(cls, participant):
        return cls(
            email=participant.email,
            name=participant.name,
            is_active=participant.is_active,
            joined_at=participant.joined_at,
            last_read_at=participant.last_read_at
        )

# Agent Schemas
class AgentInfo(BaseModel):
    """Represents an AI agent in a conversation"""
    agent_type: str
    is_active: bool
    settings: Dict[str, Any]

    @classmethod
    def from_thread_agent(cls, agent):
        return cls(
            agent_type=agent.agent_type,
            is_active=agent.is_active,
            settings=agent.settings or {}
        )

# Message Schemas
class MessageRequest(BaseModel):
    content: str
    thread_id: UUID
    email: Optional[EmailStr] = None
    agent_type: Optional[str] = None

class MessageInfoResponse(BaseModel):
    file_name: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    programming_language: Optional[str]
    file_id: Optional[str]
    chunk_count: Optional[int]
    source: Optional[str]
    participant_name: Optional[str]
    participant_email: Optional[str]
    is_owner: Optional[bool] 
    tokens_used: Optional[int]

class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    content: str
    created_at: datetime
    participant_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    message_info: Optional[MessageInfoResponse] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }

# Conversation Creation Schemas
class ConversationCreate(BaseModel):
    """Request model for creating a new conversation"""
    title: constr(min_length=1, max_length=200)
    description: Optional[str] = None
    participants: Optional[List[ParticipantCreate]] = []
    agent_types: Optional[List[str]] = []  # List of agent types

# Conversation Response Schemas
class ConversationResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantInfo]
    agents: List[AgentInfo]
    settings: Dict[str, Any]

    @classmethod
    def from_thread(cls, thread, include_participants: bool = True):
        status_mapping = {
            'active': 'ongoing',
            'archived': 'archived',
            'closed': 'ended'
        }

        participants = []
        if include_participants and hasattr(thread, 'participants'):
            participants = [
                ParticipantInfo.from_thread_participant(p)
                for p in thread.participants
                if p.is_active
            ]

        agents = []
        if hasattr(thread, 'agents'):
            agents = [
                AgentInfo.from_thread_agent(a)
                for a in thread.agents
                if a.is_active
            ]

        return cls(
            id=thread.id,
            title=thread.title,
            description=thread.description,
            owner_id=thread.owner_id,
            status=status_mapping.get(thread.status, 'ongoing'),
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            participants=participants,
            agents=agents,
            settings=thread.settings or {}
        )

class ConversationListResponse(BaseModel):
    """Response model for list of conversations"""
    items: List[ConversationResponse]
    total: int
    page: int
    size: int

    @classmethod
    def from_thread_list(cls, threads: List[Any], page: int = 1, size: int = 20):
        return cls(
            items=[ConversationResponse.from_thread(thread) for thread in threads],
            total=len(threads),
            page=page,
            size=size
        )

class RegistrationResponse(BaseModel):
    message: str
    email: str

class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    content: str
    created_at: datetime
    participant_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    message_metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True  # This allows Pydantic to convert from SQLAlchemy models
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }

# Update Schemas
class ConversationUpdate(BaseModel):
    """Request model for updating an existing conversation"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class ParticipantJoinResponse(BaseModel):
    """Response model for participant joining a conversation"""
    message: str
    conversation_id: str
    participant_token: str
    name: Optional[str]
    email: str

    class Config:
        from_attributes = True

