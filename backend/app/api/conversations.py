from fastapi import (
        APIRouter, 
        Depends, 
        HTTPException, 
        status, 
        Query
)

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, desc, and_, delete, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional, List
from uuid import uuid4, UUID
import traceback
from pydantic import BaseModel
from datetime import datetime
from app.services.notifications import NotificationService
from app.core.buffer_manager import buffer_manager
from app.services.agents import agent_manager
from app.db.session import (
        db_manager, 
        Thread, 
        ThreadParticipant, 
        ThreadAgent
)
from app.core.security import auth_manager
from app.schemas.domain.schemas import (
    Token, 
    UserAuth, 
    ConversationResponse, 
    ConversationListResponse,
    ConversationCreate,
    MessageResponse,
    MessageInfoResponse,
    ParticipantJoinResponse,
    ParticipantCreate
)
from app.models.domain.models import (
        User, 
        Message,
        MessageInfo,
        Thread
)
from app.core.security import security_manager
from app.services.rag.storage_service import rag_storage_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["conversations"])

class ParticipantData(BaseModel):
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    try:
        result = await db.execute(
            select(Thread)
            .outerjoin(ThreadParticipant)
            .outerjoin(ThreadAgent)
            .where(Thread.owner_id == current_user.id)
            .options(
                joinedload(Thread.participants),
                joinedload(Thread.agents)
            )
            .order_by(desc(Thread.updated_at))
        )
        threads = result.scalars().unique().all()
        return ConversationListResponse.from_thread_list(threads)
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    try:
        result = await db.execute(
            select(Thread)
            .outerjoin(ThreadParticipant)
            .outerjoin(ThreadAgent)
            .where(Thread.id == conversation_id)
            .options(
                joinedload(Thread.participants),
                joinedload(Thread.agents)
            )
        )
        thread = result.unique().scalar_one_or_none()
        
        if not thread:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Check if user is owner or participant
        if thread.owner_id != current_user.id and not await db_manager.is_thread_participant(
            db, conversation_id, current_user.email
        ):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this conversation"
            )
        return ConversationResponse.from_thread(thread)
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    try:
        thread = await db_manager.create_thread(
            db,
            current_user.id,
            conversation.title,
            conversation.description
        )

        # Always add MODERATOR first
        await db_manager.add_agent_to_thread(
            db,
            thread.id,
            "MODERATOR"
        )
        # Also add MONITOR agent
        await db_manager.add_agent_to_thread(
            db,
            thread.id,
            "MONITOR"
        )

        # Then add requested agents
        for agent_type in conversation.agent_types or []:
            try:
                if agent_type not in  ["MODERATOR", "MONITOR"]:  # Skip if MODERATOR or MONITOR
                    await db_manager.add_agent_to_thread(
                        db,
                        thread.id,
                        agent_type
                    )
            except KeyError:
                logger.warning(f"Invalid agent type requested: {agent_type}")
                continue

        # First add the owner as a participant
        await db_manager.add_thread_participant(
            db,
            thread.id,
            current_user.email,
            current_user.username
        )
        
        # Then add any additional participants if provided
        if conversation.participants:
            for participant in conversation.participants:
                # Skip if it's the owner's email
                if participant.email.lower() != current_user.email.lower():
                    try:
                        await db_manager.add_thread_participant(
                            db,
                            thread.id,
                            participant.email,
                            participant.name
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add participant {participant.email}: {e}")
                        continue

        await db.commit()

        # Initialize RAG collection
        await rag_storage_service.initialize_collection(
            owner_id=current_user.id
        )

        # Cache invalidation has been removed

        # Load final thread with relationships
        final_result = await db.execute(
            select(Thread)
            .options(
                joinedload(Thread.participants),
                joinedload(Thread.agents)
            )
            .where(Thread.id == thread.id)
        )
        return ConversationResponse.from_thread(final_result.unique().scalar_one())
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    try:
        # First verify the user has access to this conversation
        thread = await db.execute(
            select(Thread)
            .where(Thread.id == conversation_id)
        )
        thread = thread.scalar_one_or_none()

        if not thread:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Determine user identification method and access
        is_participant = False
        user_identifier = None

        # For regular users with standard 'id' attribute
        if hasattr(current_user, 'id'):
            user_identifier = current_user.id
            is_participant = (
                thread.owner_id == current_user.id or
                await db_manager.is_thread_participant(db, conversation_id, current_user.id)
            )

        # For participant-like objects or tokens with 'email'
        if not is_participant and hasattr(current_user, 'email'):
            user_identifier = current_user.email
            result = await db.execute(
                select(ThreadParticipant)
                .where(
                    and_(
                        ThreadParticipant.thread_id == conversation_id,
                        ThreadParticipant.email == current_user.email
                    )
                )
            )
            is_participant = result.scalar_one_or_none() is not None

        if not is_participant:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this conversation"
            )

        # First, add joinedload to the query to get message_info
        query = (
            select(Message)
            .where(Message.thread_id == conversation_id)
            .order_by(Message.created_at.asc())
            .options(joinedload(Message.message_info))  # Add this
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        # Then modify the response construction
        return [
            MessageResponse(
                id=msg.id,
                thread_id=msg.thread_id,
                content=msg.content,
                created_at=msg.created_at,
                participant_id=msg.participant_id,
                agent_id=msg.agent_id,
                message_info=MessageInfoResponse(  # Changed from metadata to message_info
                    file_name=msg.message_info.file_name if msg.message_info else None,
                    file_type=msg.message_info.file_type if msg.message_info else None,
                    file_size=msg.message_info.file_size if msg.message_info else None,
                    programming_language=msg.message_info.programming_language if msg.message_info else None,
                    file_id=msg.message_info.file_id if msg.message_info else None,
                    chunk_count=msg.message_info.chunk_count if msg.message_info else None,
                    source=msg.message_info.source if msg.message_info else None,
                    participant_name=msg.message_info.participant_name if msg.message_info else None,
                    participant_email=msg.message_info.participant_email if msg.message_info else None,
                    is_owner=msg.message_info.is_owner if msg.message_info else None,
                    tokens_used=msg.message_info.tokens_used if msg.message_info else None
                ) if msg.message_info else None
            )
            for msg in messages
        ]

    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Helper function to handle conversation changes (formerly handled cache invalidation)
async def handle_conversation_change(conversation_id: UUID, owner_id: UUID = None):
    """Handle conversation changes that previously required cache invalidation."""
    # Redis cache invalidation has been removed
    pass

@router.post("/{conversation_id}/send-invitations")
async def send_conversation_invitations(
    conversation_id: UUID,
    current_user: User = Depends(security_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
):   
    """Send invitations to conversation participants."""
    try:
        # Get thread with participants
        result = await db.execute(
            select(Thread)
            .options(
                joinedload(Thread.owner),
                joinedload(Thread.participants)
            )
            .where(Thread.id == conversation_id)
        )
        conversation = result.unique().scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
            
        if conversation.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to send invitations for this conversation"
            )

        # Get participants to invite
        result = await db.execute(
            select(ThreadParticipant)
            .where(
                and_(
                    ThreadParticipant.thread_id == conversation_id,
                    ThreadParticipant.email != current_user.email  # Don't send to the owner
                )
            )
        )
        participants = result.scalars().all()
        
        if not participants:
            raise HTTPException(
                status_code=400,
                detail="No participants found to invite"
            )

        notification_service = NotificationService()
        results = {}

        for participant in participants:
            try:
                # Regenerate invitation token for existing participant
                invitation_token = security_manager.create_invitation_token({
                    "thread_id": str(conversation_id),
                    "email": participant.email
                })

                # Update participant's invitation token if needed
                participant.invitation_token = invitation_token
                participant.invitation_sent_at = datetime.utcnow()
                
                # Send new invitation
                success = await notification_service.send_thread_invitation(
                    conversation, 
                    participant
                )
                
                results[participant.email] = success
                
            except Exception as e:
                logger.error(f"Error re-inviting {participant.email}: {e}")
                results[participant.email] = False

        await db.commit()
        
        # Handle conversation change (formerly invalidated caches)
        await handle_conversation_change(conversation_id, current_user.id)
        
        # Log the results
        logger.info(f"Invitation results for conversation {conversation_id}: {results}")
        
        successful_invites = sum(1 for success in results.values() if success)
        failed_invites = sum(1 for success in results.values() if not success)
        
        return {
            "message": "Invitations processed",
            "results": {
                "successful": successful_invites,
                "failed": failed_invites,
                "details": results
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error sending invitations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send invitations: {str(e)}"
        )

@router.post("/register", response_model=Token)
async def register_user(
    user_data: UserAuth,
    db: AsyncSession = Depends(db_manager.get_session)
):
    try:
        existing_user = await db_manager.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        hashed_password = auth_manager.get_password_hash(user_data.password)
        user = await db_manager.create_user(
            db, user_data.username, user_data.email, hashed_password
        )
        
        access_token = auth_manager.create_access_access_token(data={"sub": user.username})
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_manager.get_session)
):
    user = await auth_manager.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in"
        )
        
    access_token = auth_manager.create_access_token(data={"sub": user.username})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username
    )

class JoinRequest(BaseModel):
    invitation_token: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class ParticipantJoinResponse(BaseModel):
    message: str
    conversation_id: str
    participant_token: str
    name: Optional[str]
    email: str

    class Config:
        from_attributes = True
    
@router.post("/join", response_model=ParticipantJoinResponse)
async def join_conversation(
    join_data: JoinRequest,
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Join a conversation using an invitation token."""
    try:
        # Decode and verify the invitation token
        payload = security_manager.verify_invitation_token(join_data.invitation_token)
        if not payload:
            logger.error("Invalid or expired invitation token")
            raise HTTPException(status_code=400, detail="Invalid or expired invitation token")

        thread_id = UUID(payload.get("thread_id"))
        email = payload.get("email")

        if not thread_id or not email:
            logger.error("Invalid invitation token payload: missing thread_id or email")
            raise HTTPException(status_code=400, detail="Invalid invitation token")

        # Log the details for debugging
        logger.info(f"Participant Join Attempt: thread_id={thread_id}, email={email}")

        # Debug: Check all participants in DB for the thread
        all_participants = await db.execute(
            select(ThreadParticipant).where(ThreadParticipant.thread_id == thread_id)
        )
        all_participants = all_participants.scalars().all()
        logger.error(f"DEBUG: Participants in DB for thread_id {thread_id}: {all_participants}")

        # Ensure invitation exists for the participant
        result = await db.execute(
            select(ThreadParticipant)
            .where(ThreadParticipant.thread_id == thread_id)
            .where(func.lower(ThreadParticipant.email) == func.lower(email))
        )

        participant = result.scalar_one_or_none()

        if not participant:
            logger.error(f"Invitation not found for thread_id: {thread_id}, email: {email}")
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Debug: Validate the stored invitation token in DB
        logger.error(f"Stored invitation_token in DB: {participant.invitation_token}")

        # Ensure participant name is updated if provided
        if join_data.name:
            participant.name = join_data.name
            await db.commit()
            logger.info(f"Participant name updated: {participant.name}")

        # Generate participant-specific token
        participant_token = security_manager.create_participant_token(
            thread_id=thread_id,
            email=email,
            name=join_data.name
        )

        # Handle conversation change (formerly invalidated caches)
        await handle_conversation_change(thread_id)

        # Log the generated token for verification
        logger.info(f"Generated Participant Token: {participant_token}")
        return ParticipantJoinResponse(
            message="Successfully joined conversation",
            conversation_id=str(thread_id),
            participant_token=participant_token,
            name=join_data.name or email,
            email=email
        )

    except Exception as e:
        logger.error(f"Error joining conversation: {e}")
        await db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
           
@router.post("/{conversation_id}/add-participant")
async def add_participant(
    conversation_id: UUID,
    participant_data: ParticipantData,
    current_user: User = Depends(security_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Add a new participant or resend invitation to an existing participant."""
    # Explicit validation
    if not participant_data or not participant_data.email:
        raise HTTPException(status_code=400, detail="Email is required")

    email = participant_data.email
    name = participant_data.name

    # Explicit type checking
    if not isinstance(email, str):
        raise HTTPException(status_code=422, detail="Invalid email format")

    try:
        # Verify conversation ownership
        thread = await db_manager.get_thread(db, conversation_id)
        if thread.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the conversation owner can add participants"
            )

        # Explicit participant creation logic
        result = await db.execute(
            select(ThreadParticipant)
            .where(
                and_(
                    ThreadParticipant.thread_id == conversation_id,
                    ThreadParticipant.email == email
                )
            )
        )
        participant = result.scalar_one_or_none()
        
        # Regenerate invitation token
        invitation_token = security_manager.create_invitation_token({
            "thread_id": str(conversation_id),
            "email": email
        })

        if participant:
            # Update existing participant's invitation token
            participant.invitation_token = invitation_token
            participant.invitation_sent_at = datetime.utcnow()
        else:
            # Create new participant
            participant = ThreadParticipant(
                id=uuid4(),
                thread_id=conversation_id,
                email=email,
                name=name,
                joined_at=datetime.utcnow(),
                is_active=True,
                invitation_token=invitation_token,
                invitation_sent_at=datetime.utcnow()
            )
            db.add(participant)

        # Send invitation
        notification_service = NotificationService()
        await notification_service.send_thread_invitation(thread, participant)

        await db.commit()

        # Handle conversation change (formerly invalidated caches)
        await handle_conversation_change(conversation_id, current_user.id)

        return {"message": f"Invitation sent to {email}"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add/invite participant: {str(e)}"
        )

@router.delete("/{conversation_id}/remove-participant")
async def remove_participant(
    conversation_id: UUID,
    participant_data: dict,
    current_user: User = Depends(security_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Remove a participant from a conversation."""
    email = participant_data.get('email')

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        # Verify conversation ownership
        thread = await db_manager.get_thread(db, conversation_id)
        if thread.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the conversation owner can remove participants"
            )

        # Find and remove the participant
        result = await db.execute(
            select(ThreadParticipant)
            .where(
                and_(
                    ThreadParticipant.thread_id == conversation_id,
                    ThreadParticipant.email == email
                )
            )
        )
        participant = result.scalar_one_or_none()

        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found")

        await db.delete(participant)
        await db.commit()

        # Handle conversation change (formerly invalidated caches)
        await handle_conversation_change(conversation_id, current_user.id)

        return {"message": "Participant removed successfully"}

    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing participant: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove participant: {str(e)}"
        )

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Delete a specific conversation."""
    try:
        # First, verify the conversation exists and belongs to the current user
        result = await db.execute(
            select(Thread)
            .where(
                and_(
                    Thread.id == conversation_id,
                    Thread.owner_id == current_user.id
                )
            )
        )
        thread = result.scalar_one_or_none()

        if not thread:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found or you are not authorized to delete it"
            )

        # Store owner_id before deletion for cache invalidation
        owner_id = thread.owner_id

        await db.execute(
            delete(MessageInfo).where(
                MessageInfo.message_id.in_(
                    select(Message.id).where(Message.thread_id == conversation_id)
                )
            )
        )

        # Then delete messages
        await db.execute(
            delete(Message).where(Message.thread_id == conversation_id)
        )

        # Delete associated participants
        await db.execute(
            delete(ThreadParticipant).where(ThreadParticipant.thread_id == conversation_id)
        )

        # Delete associated agents
        await db.execute(
            delete(ThreadAgent).where(ThreadAgent.thread_id == conversation_id)
        )

        # Finally, delete the conversation itself
        await db.delete(thread)
        await db.commit()
       
        buffer_manager.delete_conversation(conversation_id)
        
        # Handle conversation change (formerly invalidated caches)
        await handle_conversation_change(conversation_id, owner_id)
        
        return None  # No content, as specified by 204 status code

    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting conversation: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )
