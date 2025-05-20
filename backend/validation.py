from pydantic import BaseModel, Field, EmailStr, constr, validator
from typing import Optional, List, Dict, Union
from datetime import datetime
from uuid import UUID
from enum import Enum
from models import AgentType, ThreadStatus

class ParticipantCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class ThreadCreate(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: Optional[str] = None
    participants: List[ParticipantCreate]
    agent_types: List[AgentType]

class MessageBase(BaseModel):
    content: constr(min_length=1, max_length=10000)
    thread_id: UUID
    metadata: Optional[Dict] = Field(default_factory=dict)

class UserMessageCreate(MessageBase):
    pass

class ParticipantMessageCreate(MessageBase):
    email: EmailStr

class AgentMessageCreate(MessageBase):
    agent_type: AgentType

class ThreadResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    owner_id: UUID
    status: ThreadStatus
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantCreate]
    agents: List[Dict[str, Union[AgentType, bool]]]

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    content: str
    created_at: datetime
    user_id: Optional[UUID] = None
    participant_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    metadata: Dict = {}

    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    type: str
    content: Dict
    identifier: Union[UUID, str]  # Can be user_id or email
    is_owner: bool = False

    @validator('type')
    def validate_message_type(cls, v):
        allowed_types = {'message', 'typing', 'read', 'join', 'leave'}
        if v not in allowed_types:
            raise ValueError(f'Message type must be one of {allowed_types}')
        return v
