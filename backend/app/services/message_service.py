from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import logging
from fastapi import HTTPException

from models import Message, ThreadParticipant, ThreadAgent, Thread

logger = logging.getLogger(__name__)

class MessagePersistenceManager:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def save_message(self, message_data: Dict[str, Any]) -> Message:
        """Save a message from any source (user, participant, or agent)."""
        try:
            # Validate message source
            sources = [
                message_data.get('user_id'),
                message_data.get('participant_id'),
                message_data.get('agent_id')
            ]
            source_count = sum(1 for source in sources if source is not None)
            if source_count != 1:
                raise ValueError("Message must have exactly one source (user, participant, or agent)")

            message = Message(
                thread_id=message_data['thread_id'],
                user_id=message_data.get('user_id'),
                participant_id=message_data.get('participant_id'),
                agent_id=message_data.get('agent_id'),
                content=message_data['content'],
                message_metadata=message_data.get('metadata', {}),
                created_at=datetime.utcnow()
            )
            
            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)
            return message
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving message: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error saving message: {str(e)}"
            )

    async def get_thread_messages(
        self,
        thread_id: UUID,
        limit: int = 50,
        before: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from a thread with proper loading of relationships."""
        try:
            query = (
                select(Message)
                .where(Message.thread_id == thread_id)
                .options(
                    joinedload(Message.participant),
                    joinedload(Message.agent)
                )
                .order_by(desc(Message.created_at))
            )

            if before:
                query = query.where(Message.created_at < before)

            query = query.limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving thread messages: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving messages: {str(e)}"
            )

    async def verify_message_sender(
        self,
        thread_id: UUID,
        email: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> Union[ThreadParticipant, ThreadAgent, None]:
        """Verify and get message sender (participant or agent)."""
        try:
            if email:
                result = await self.db.execute(
                    select(ThreadParticipant)
                    .where(
                        and_(
                            ThreadParticipant.thread_id == thread_id,
                            ThreadParticipant.email == email,
                            ThreadParticipant.is_active == True
                        )
                    )
                )
                return result.scalar_one_or_none()
            elif agent_type:
                result = await self.db.execute(
                    select(ThreadAgent)
                    .where(
                        and_(
                            ThreadAgent.thread_id == thread_id,
                            ThreadAgent.agent_type == agent_type,
                            ThreadAgent.is_active == True
                        )
                    )
                )
                return result.scalar_one_or_none()
            return None
        except Exception as e:
            logger.error(f"Error verifying message sender: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error verifying message sender: {str(e)}"
            )
