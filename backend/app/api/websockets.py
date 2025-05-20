from fastapi import APIRouter, WebSocket, Depends, HTTPException
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Set, Optional, List, Union
from uuid import UUID, uuid4
from datetime import datetime
import json
import asyncio
import logging
import traceback
import tiktoken
import re
from app.core.security import auth_manager
from app.core.config import settings
from app.core.input_sanitizer import input_sanitizer
from app.services.agents.agent_manager import agent_manager, AGENTS
from app.core.websocket_queue import connection_health
from app.core.progress_manager import progress_manager
from app.db.session import db_manager, ThreadAgent, ThreadParticipant, User, Message, MessageInfo, Thread, AsyncSessionLocal
from app.services.rag import rag_storage_service
# Redis services and queues have been removed
# from app.services.redis.redis_service import redis_service
# from app.services.redis.worker import Queues

logger = logging.getLogger(__name__)
router = APIRouter()

def process_agent_message_content(content: str) -> str:
    """
    Process agent message content to ensure proper display of code in FileDisplay.
    
    Args:
        content: The raw message content from the agent
        
    Returns:
        Processed content with proper script tag for FileDisplay if needed
    """
    # Check if content already has a script tag for FileDisplay
    if '<script type="application/vnd.ant.editable">' in content:
        return content
    
    # Check for markdown code blocks
    code_block_pattern = r"```(\w+)?\s*\n([\s\S]*?)\n```"
    
    def replace_code_block(match):
        language = match.group(1) or "text"
        code = match.group(2)
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = get_file_extension(language)
        filename = f"code_{timestamp}.{file_extension}"
        
        # Create the JSON data for FileDisplay
        editable_data = {
            "content": code,
            "fileName": filename,
            "fileType": file_extension
        }
        
        # Return script tag that will be rendered as FileDisplay
        return f"<script type=\"application/vnd.ant.editable\">{json.dumps(editable_data)}</script>"
    
    # Replace all code blocks with script tags
    processed_content = re.sub(code_block_pattern, replace_code_block, content)
    
    return processed_content

def get_file_extension(language: str) -> str:
    """Get the appropriate file extension for the given programming language."""
    extensions = {
        'python': 'py',
        'javascript': 'js',
        'typescript': 'ts',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'c++': 'cpp',
        'csharp': 'cs',
        'c#': 'cs',
        'go': 'go',
        'ruby': 'rb',
        'php': 'php',
        'swift': 'swift',
        'kotlin': 'kt',
        'rust': 'rs',
        'scala': 'scala',
        'perl': 'pl',
        'julia': 'jl',
        'lua': 'lua',
        'haskell': 'hs',
        'elixir': 'ex',
        'erlang': 'erl',
        'dart': 'dart',
        'html': 'html',
        'css': 'css',
        'sql': 'sql',
        'bash': 'sh',
        'shell': 'sh',
        'yaml': 'yml',
        'json': 'json',
        'markdown': 'md',
        'text': 'txt'
    }
    return extensions.get(language.lower(), 'txt')

async def _handle_typing_status(
    db: AsyncSession,
    conversation_id: UUID,
    sender,  # Can be User, ParticipantUser, or ThreadAgent
    is_typing: bool
) -> None:
    """Broadcast typing status with proper async handling."""
    try:
        # Check if db connection is still valid
        if not db.is_active:
            logger.warning("Database session expired, creating new session")
            await db.close()
            async with AsyncSessionLocal() as new_db:
                return await _handle_typing_status(new_db, conversation_id, sender, is_typing)

        if isinstance(sender, ThreadAgent):
            # Agent - use agent_type@system.local as identifier
            identifier = f"{sender.agent_type.lower()}@system.local"
            is_owner = False
            metadata = {"agent_type": sender.agent_type}
        elif not isinstance(sender, User):
            # ParticipantUser - direct attribute access is safe
            identifier = sender.email
            is_owner = False
            metadata = {"participant_name": sender.name}
        else:
            # SQLAlchemy User - do a proper async load with error handling
            try:
                async with db.begin():
                    result = await db.execute(
                        select(User.email).where(User.id == sender.id)
                    )
                    identifier = result.scalar_one()
                    is_owner = True
                    metadata = {}
            except Exception as db_error:
                logger.error(f"Database error in typing status: {db_error}")
                # Fallback to using stored user email if available
                identifier = getattr(sender, 'email', str(sender.id))
                is_owner = True
                metadata = {}

        # Ensure we have a valid identifier before broadcasting
        if not identifier:
            logger.error(f"No valid identifier found for sender: {sender}")
            return

        await connection_health.broadcast(
            conversation_id,
            {
                "type": "typing_status",
                "identifier": identifier,
                "is_owner": is_owner,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat(),
                **metadata
            }
        )
    except Exception as e:
        logger.error(f"Error handling typing status: {e}")
        logger.error(traceback.format_exc())
        # Don't re-raise the exception to prevent websocket disconnection

async def _handle_editor_open(
    db: AsyncSession,
    conversation_id: UUID,
    sender,
    file_name: str,
    file_type: str,
    content: str
) -> None:
    """Process editor open event and broadcast to all clients."""
    try:
        # Determine sender identity
        if isinstance(sender, ThreadAgent):
            identifier = f"{sender.agent_type.lower()}@system.local"
            sender_name = sender.agent_type
            sender_email = identifier
        elif not isinstance(sender, User):
            # ParticipantUser
            identifier = sender.email
            sender_name = sender.name or sender.email
            sender_email = sender.email
        else:
            # User
            identifier = sender.email
            sender_name = getattr(sender, 'username', None) or sender.email
            sender_email = sender.email

        # Broadcast the editor open event to all clients
        await connection_health.broadcast(
            conversation_id,
            {
                "type": "editor_open",
                "fileName": file_name,
                "fileType": file_type,
                "content": content,
                "identifier": identifier,
                "timestamp": datetime.utcnow().isoformat(),
                "sender": {
                    "name": sender_name,
                    "email": sender_email
                }
            }
        )
        logger.info(f"Editor open event broadcast for {file_name} in conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Error handling editor open: {e}")
        logger.error(traceback.format_exc())

# In websockets.py - update _handle_editor_change
async def _handle_editor_change(
    db: AsyncSession,
    conversation_id: UUID,
    sender,
    file_name: str,
    content: str
) -> None:
    """Process editor change event and broadcast to all clients."""
    try:
        # Determine sender identity
        if isinstance(sender, ThreadAgent):
            identifier = f"{sender.agent_type.lower()}@system.local"
            sender_name = sender.agent_type
            sender_email = identifier
        elif not isinstance(sender, User):
            # ParticipantUser
            identifier = sender.email
            sender_name = sender.name or sender.email
            sender_email = sender.email
        else:
            # User
            identifier = sender.email
            sender_name = getattr(sender, 'username', None) or sender.email
            sender_email = sender.email

        # Log message details for debugging
        logger.info(f"Editor change from {sender_email} for {file_name} in conversation {conversation_id}")

        # Broadcast the editor change event to all clients
        await connection_health.broadcast(
            conversation_id,
            {
                "type": "editor_change",  # Explicitly ensure this is editor_change
                "fileName": file_name,
                "content": content,
                "identifier": identifier,
                "timestamp": datetime.utcnow().isoformat(),
                "sender": {
                    "name": sender_name,
                    "email": sender_email
                }
            }
        )
        logger.debug(f"Editor change event broadcast for {file_name} in conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Error handling editor change: {e}")
        logger.error(traceback.format_exc())

async def _handle_editor_close(
    db: AsyncSession,
    conversation_id: UUID,
    sender,
    file_name: str
) -> None:
    """Process editor close event and broadcast to all clients."""
    try:
        # Determine sender identity
        if isinstance(sender, ThreadAgent):
            identifier = f"{sender.agent_type.lower()}@system.local"
            sender_name = sender.agent_type
            sender_email = identifier
        elif not isinstance(sender, User):
            # ParticipantUser
            identifier = sender.email
            sender_name = sender.name or sender.email
            sender_email = sender.email
        else:
            # User
            identifier = sender.email
            sender_name = getattr(sender, 'username', None) or sender.email
            sender_email = sender.email

        # Broadcast the editor close event to all clients
        await connection_health.broadcast(
            conversation_id,
            {
                "type": "editor_close",
                "fileName": file_name,
                "identifier": identifier,
                "timestamp": datetime.utcnow().isoformat(),
                "sender": {
                    "name": sender_name,
                    "email": sender_email
                }
            }
        )
        logger.info(f"Editor close event broadcast for {file_name} in conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Error handling editor close: {e}")
        logger.error(traceback.format_exc())

async def _handle_user_message(
    db: AsyncSession,
    conversation_id: UUID,
    user: User,
    content: str,
    conversation_agents: List[ThreadAgent],
    message_metadata: Optional[Dict] = None
) -> None:
    """Process and handle user messages with non-blocking agent response processing."""
    try:
        if not await db.connection():
            await db.close()
            db = await AsyncSessionLocal()

        privacy_enabled = await connection_health.is_private(conversation_id)

        # Get conversation for token tracking
        conversation = await db.execute(
            select(Thread).where(Thread.id == conversation_id)
        )
        thread = conversation.scalar_one()

        encoding = tiktoken.get_encoding("gpt2")
        tokens_used = len(encoding.encode(content))

        # Track token usage
        await db.execute(
            update(User)
            .where(User.id == thread.owner_id)
            .values(tokens_consumed=User.tokens_consumed + tokens_used)
        )

        # Handle message persistence if not private
        message_id = str(uuid4())
        combined_metadata = {}
        
        if not privacy_enabled:
            # Get participant record for this user in this thread
            result = await db.execute(
                select(ThreadParticipant)
                .where(and_(
                    ThreadParticipant.thread_id == conversation_id,
                    ThreadParticipant.email == user.email
                ))
            )
            participant = result.scalar_one_or_none()
            
            if not participant:
                # Fall back to creating a message without participant_id
                logger.warning(f"No participant record found for {user.email} in thread {conversation_id}")
                message = Message(
                    thread_id=conversation_id,
                    content=content,
                    created_at=datetime.utcnow()
                )
            else:
                # Create message with participant_id
                message = Message(
                    thread_id=conversation_id,
                    participant_id=participant.id,
                    content=content,
                    created_at=datetime.utcnow()
                )
                
            db.add(message)
            await db.flush()  # This ensures we have message.id
            
            # Create message info with additional metadata
            message_info = MessageInfo(
                message_id=message.id,
                source="user",
                participant_name=getattr(user, 'name', None) or user.email,
                participant_email=user.email,
                is_owner=True,
                **{k: v for k, v in message_metadata.items() if k in MessageInfo.__table__.columns}
            )
            db.add(message_info)
            await db.flush()
            
            # Use the database ID for the message
            message_id = str(message.id)
            combined_metadata = message_metadata

        # Broadcast message
        broadcast_user_message = {
            "type": "message",
            "content": content,
            "id": message_id,
            "identifier": user.email,
            "is_owner": True,
            "email": user.email,
            "timestamp": datetime.utcnow().isoformat(),
            "message_metadata": combined_metadata if not privacy_enabled else None
        }
        await connection_health.broadcast(conversation_id, broadcast_user_message)
        agent_types = list(map(lambda x: x.agent_type, conversation_agents))

        # IMPROVED: Non-blocking agent response processing
        if content.startswith('@'):
            # Split into first word and rest of message
            parts = content.split(' ', 1)
            if len(parts) < 2:
                return  # No message content after @

            target = parts[0][1:]  # Remove @ symbol
            message_content = parts[1]

            if not target:  # Case: "@ message" - route to moderator
                # Check if any agents are available for this conversation
                if not agent_types or len(agent_types) == 0:
                    # No agents available for this conversation
                    no_agents_message = {
                        "type": "message",
                        "content": "No agents are available for this conversation. Please contact support.",
                        "id": str(uuid4()),
                        "identifier": "system",
                        "is_owner": False,
                        "email": "system@system.local",
                        "agent_type": "SYSTEM",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_health.broadcast(conversation_id, no_agents_message)
                    return
                    
                # First send a typing indicator
                typing_message = {
                    "type": "typing_status",
                    "identifier": "moderator@system.local",  # Will be updated by actual agent
                    "is_owner": False,
                    "is_typing": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_type": "MODERATOR"  # Initially set to MODERATOR
                }
                await connection_health.broadcast(conversation_id, typing_message)
                
                # Log that we're processing the message
                logger.info(f"Starting agent processing task for conversation {conversation_id} with automatic agent selection")
                
                # Create a non-blocking background task
                asyncio.create_task(
                    _process_agent_conversation(
                        message_content=message_content,
                        agent_types=agent_types,
                        mention=None,
                        conversation_id=conversation_id,
                        thread_owner_id=thread.owner_id,
                        privacy_enabled=privacy_enabled
                    )
                )

            else:  # Case: "@AGENT message" - route to specific agent
                target_agent = target.upper()
                target_agent_obj = next(
                    (a for a in conversation_agents if a.agent_type == target_agent),
                    None
                )
                if target_agent_obj:
                    # First send a typing indicator for the specific agent
                    typing_message = {
                        "type": "typing_status", 
                        "identifier": f"{target_agent.lower()}@system.local",
                        "is_owner": False,
                        "is_typing": True,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent_type": target_agent
                    }
                    await connection_health.broadcast(conversation_id, typing_message)
                    
                    # Log that we're processing the message
                    logger.info(f"Starting agent processing task for conversation {conversation_id} with agent {target_agent}")
                    
                    # Create a non-blocking background task
                    asyncio.create_task(
                        _process_agent_conversation(
                            message_content=message_content,
                            agent_types=agent_types,
                            mention=target_agent,
                            conversation_id=conversation_id,
                            thread_owner_id=thread.owner_id,
                            privacy_enabled=privacy_enabled
                        )
                    )
                else:
                    available_agent_message = _available_agents(conversation_agents, target_agent)
                    await connection_health.broadcast(conversation_id, available_agent_message)
        elif content.startswith('?'):
            broadcast_help_message = _help_message()
            await connection_health.broadcast(conversation_id, broadcast_help_message)
        else:
            # Messages without @ prefix are broadcast without agent response
            pass  # Message was already broadcast above

        await db.commit()

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        logger.error(traceback.format_exc())
        await db.rollback()
        raise

async def _process_agent_conversation(
    message_content: str,
    agent_types: List[str],
    mention: Optional[str],
    conversation_id: UUID,
    thread_owner_id: UUID,
    privacy_enabled: bool
) -> None:
    """Background task that processes agent conversations without blocking."""
    try:
        # Get a fresh database session for this task
        async with AsyncSessionLocal() as db:
            encoding = tiktoken.get_encoding("gpt2")
            
            # Apply input sanitization at the websocket level as well
            # This gives us double protection (here and in agent_manager)
            sanitized_content, is_suspicious, detected_patterns = input_sanitizer.sanitize_input(message_content)
            
            # Log any detected suspicious patterns
            if is_suspicious:
                logger.warning(f"WebSocket layer detected potential prompt injection in conversation {conversation_id}: {detected_patterns}")
                
                # If high-risk patterns are detected, we can choose to block the message entirely
                if any(p in str(detected_patterns).lower() for p in ['ignore', 'system prompt', 'jailbreak']):
                    logger.error(f"High-risk prompt injection blocked at WebSocket layer: {detected_patterns}")
                    # Send a system message to the conversation
                    await connection_health.broadcast(
                        conversation_id,
                        {
                            "type": "message",
                            "content": "Message blocked due to security concerns. Please avoid using system instructions or prompt manipulation techniques.",
                            "id": str(uuid4()),
                            "identifier": "system",
                            "is_owner": False, 
                            "email": "system@system.local",
                            "agent_type": "SYSTEM",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    # Clear the typing indicator
                    await connection_health.broadcast(
                        conversation_id,
                        {
                            "type": "typing_status",
                            "identifier": f"{(mention or 'moderator').lower()}@system.local",
                            "is_owner": False,
                            "is_typing": False,
                            "timestamp": datetime.utcnow().isoformat(),
                            "agent_type": mention or "MODERATOR"
                        }
                    )
                    return
            
            # Define a streaming callback function
            async def streaming_callback(token: str):
                """Send token updates to the WebSocket in real-time."""
                if token and len(token.strip()) > 0:
                    try:
                        # Only broadcast non-empty tokens
                        await connection_health.broadcast(
                            conversation_id,
                            {
                                "type": "token",
                                "token": token,
                                "conversation_id": str(conversation_id),
                                "agent_type": mention or "PROCESSING",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    except Exception as broadcast_error:
                        logger.error(f"Error broadcasting token: {broadcast_error}")
            
            # Process conversation with the agent - sanitization will happen again in agent_manager
            agent_type, agent_response = await agent_manager.process_conversation(
                sanitized_content,  # Use the sanitized content here
                agent_types,
                AGENTS,
                mention=mention,
                db=db,
                thread_id=str(conversation_id),
                owner_id=thread_owner_id,
                response_callback=streaming_callback if not privacy_enabled else None
            )
            
            # Clear typing indicator
            typing_end_message = {
                "type": "typing_status",
                "identifier": f"{agent_type.lower()}@system.local",
                "is_owner": False,
                "is_typing": False,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_type": agent_type
            }
            await connection_health.broadcast(conversation_id, typing_end_message)
            
            # Track token usage
            agent_tokens = len(encoding.encode(agent_response))
            await db.execute(
                update(User)
                .where(User.id == thread_owner_id)
                .values(tokens_consumed=User.tokens_consumed + agent_tokens)
            )
            
            # Handle the agent response
            await _handle_agent_response(
                db,
                conversation_id,
                agent_type,
                agent_response,
                privacy_enabled
            )
            
    except Exception as e:
        logger.error(f"Error in background agent processing task: {e}")
        logger.error(traceback.format_exc())
        
        # Clear any active typing indicator
        agent_id = mention.lower() if mention else "moderator"
        typing_end_message = {
            "type": "typing_status",
            "identifier": f"{agent_id}@system.local",
            "is_owner": False,
            "is_typing": False,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": mention or "MODERATOR"
        }
        await connection_health.broadcast(conversation_id, typing_end_message)
        
        # Send error message to the conversation
        error_message = {
            "type": "message",
            "content": f"I'm sorry, there was an error processing your request: {str(e)}",
            "id": str(uuid4()),
            "identifier": "system",
            "is_owner": False,
            "email": "system@system.local",
            "agent_type": "SYSTEM",
            "timestamp": datetime.utcnow().isoformat()
        }
        await connection_health.broadcast(conversation_id, error_message)

async def _handle_agent_response(
    db: AsyncSession,
    conversation_id: UUID,
    agent_type: str,
    content: str,
    is_private: bool
) -> None:
    """Process and handle agent responses."""
    try:
        # Process content to ensure proper code display
        content = process_agent_message_content(content)
        
        result = await db.execute(
            select(ThreadAgent)
            .where(and_(
                ThreadAgent.thread_id == conversation_id,
                ThreadAgent.agent_type == agent_type
            ))
        )
        agent = result.scalar_one_or_none()

        if not agent:
            result = await db.execute(
                select(ThreadAgent)
                .where(and_(
                    ThreadAgent.thread_id == conversation_id,
                    ThreadAgent.agent_type == 'MODERATOR'))
            )
            agent = result.scalar_one_or_none()

        if not agent:
            raise ValueError(f"No agent found for conversation {conversation_id}")

        # Generate message ID - either from persisted message or temporary
        message_id = str(uuid4())
        if not is_private:
            message = Message(
                thread_id=conversation_id,
                agent_id=agent.id,
                content=content,
                created_at=datetime.utcnow()
            )
            db.add(message)
            await db.flush()  # This ensures we have message.id
    
            # Create the associated MessageInfo record
            message_info = MessageInfo(
                message_id=message.id,
                source=agent.agent_type,  # Using source field to store agent_type
                # Add any other relevant fields you want to track for agent messages
            )
            db.add(message_info)
            await db.flush()
    
            message_id = str(message.id)

        # Always broadcast response
        broadcast_agent_message = {
            "type": "message",
            "content": content,
            "id": message_id,
            "identifier": str(agent.id),
            "is_owner": False,
            "email": f"{agent_type.lower()}@system.local",
            "agent_type": agent.agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        await connection_health.broadcast(conversation_id, broadcast_agent_message)

        await db.commit()

    except Exception as e:
        logger.error(f"Error in handle_agent_response: {e}")
        logger.error(traceback.format_exc())
        await db.rollback()
        raise

def _help_message():
    help_message = """Message Commands:
        - Start with '@AGENT' to direct your message to a specific Agent
            (If the Agent isn't found, you'll see a list of available Agents)
        - Start with '@ ' to have the Moderator select the best Agent or combination of agents to respond
        - Messages without '@' will be broadcast to all participants without Agent responses
        - Start with '?' to see this help message"""

    broadcast_help_message = {
        "type": "message",
        "content": help_message,
        "id": str(uuid4()),
        "identifier": "system",
        "is_owner": False,
        "email": "system@system.local",
        "agent_type": "SYSTEM",
        "timestamp": datetime.utcnow().isoformat()
    }
    return broadcast_help_message


def _available_agents(conversation_agents, target_agent):
    available_agents = [a.agent_type for a in conversation_agents]
    response = (
        f"Agent '{target_agent}' not found.\n"
        f"Available agents: {', '.join(sorted(available_agents))}"
    )
    available_agents_message = {
        "type": "message", 
        "content": response,
        "id": str(uuid4()),
        "identifier": "system",
        "is_owner": False,
        "email": "system@system.local",
        "agent_type": "SYSTEM",
        "timestamp": datetime.utcnow().isoformat()
    }         
    return available_agents_message

@router.websocket("/ws/progress/{thread_id}")
async def websocket_progress_endpoint(
    websocket: WebSocket,
    thread_id: str
):
    try:
        await progress_manager.connect(websocket, thread_id)
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket, thread_id)


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str,
    connection_id: str,
    db: AsyncSession = Depends(db_manager.get_session)
):
    ws_connection_id = None
    connection_active = False
    try:
        # Step 1: Accept the WebSocket connection FIRST
        await websocket.accept()

        # Step 2: Authenticate user
        try:
            async with asyncio.timeout(10):
                user = await auth_manager.get_current_user_ws(token, db)
                if not user:
                    participant = await auth_manager.get_participant_from_token(token, db)
                    if participant:
                        user = type('ParticipantUser', (), {
                            'email': participant.email,
                            'name': participant.name,
                            'id': participant.id,
                        })
                    else:
                        logger.error("Authentication failed")
                        await websocket.close(code=4001, reason="Authentication failed")
                        return
        except Exception as auth_error:
            logger.error(f"Authentication error: {auth_error}")
            await websocket.close(code=4001, reason="Authentication error")
            return

        # Step 3: Verify conversation and participant access
        try:
            async with asyncio.timeout(10):
                # Verify conversation exists
                conversation = await db_manager.get_thread(db, conversation_id)
                if not conversation:
                    logger.error(f"Conversation {conversation_id} not found")
                    await websocket.close(code=4002, reason="Conversation not found")
                    return

                # Verify participant access
                result = await db.execute(
                    select(ThreadParticipant)
                    .where(
                        and_(
                            ThreadParticipant.thread_id == conversation_id,
                            ThreadParticipant.email == user.email
                        )
                    )
                )
                is_participant = result.scalar_one_or_none() is not None

                if not is_participant:
                    logger.error(f"User {user.email} is not a participant")
                    await websocket.close(code=4003, reason="Not a participant")
                    return
        except Exception as access_error:
            logger.error(f"Access verification error: {access_error}")
            await websocket.close(code=4004, reason="Access verification failed")
            return

        # Step 4: Register with connection manager
        try:
            async with asyncio.timeout(30):
                ws_connection_id = await connection_health.enqueue_connection(
                    websocket,
                    conversation_id,
                    user.email
                )

                if not ws_connection_id:
                    logger.error("Failed to register connection")
                    await websocket.close(code=4005, reason="Connection registration failed")
                    return

                connection_active = True
                conversation_agents = await db_manager.get_thread_agents(db, conversation_id)
        except Exception as reg_error:
            logger.error(f"Connection registration error: {reg_error}")
            await websocket.close(code=4006, reason="Connection registration error")
            return

        # Message handling loop
        while connection_active:
            try:
                async with asyncio.timeout(connection_health.CONNECTION_TIMEOUT):
                    message = await websocket.receive_json()
                    message_type = message.get("type")
                    if not message_type:
                        continue

                    if message_type == "message":
                        content = message.get('content')
                        if content:
                            # Extract metadata from message
                            message_metadata = {}
                            # Add file metadata if present
                            file_metadata = message.get('message_metadata')
                            if file_metadata:
                                # Handle both direct metadata and nested structure
                                message_metadata.update({
                                    'file_name': file_metadata.get('filename', file_metadata.get('file_name')),
                                    'file_type': file_metadata.get('mime_type', file_metadata.get('file_type')),
                                    'file_size': file_metadata.get('size', file_metadata.get('file_size')),
                                    'programming_language': file_metadata.get('programming_language'),
                                    'file_id': file_metadata.get('id', file_metadata.get('file_id')),
                                    'chunk_count': file_metadata.get('chunk_count')
                                })
                                
                                # Log the metadata for debugging
                                logger.info(f"File metadata: {file_metadata}")
                                logger.info(f"Processed message_metadata: {message_metadata}")

                            # Add any custom metadata fields
                            custom_metadata = message.get('metadata', {})
                            if custom_metadata:
                                message_metadata.update(custom_metadata)

                            await _handle_user_message(
                                db=db,
                                conversation_id=conversation_id,
                                user=user,
                                content=content,
                                conversation_agents=conversation_agents,
                                message_metadata=message_metadata
                            )
                    elif message_type == "typing_status":
                        await _handle_typing_status(
                            db,
                            conversation_id,
                            user,
                            message.get("is_typing", False)
                        )
                    elif message_type == "set_privacy":
                        is_private = message.get("is_private", False)
                        await connection_health.set_privacy(conversation_id, is_private)
                        await connection_health.broadcast(
                            conversation_id,
                            {
                                "type": "privacy_changed",
                                "is_private": is_private,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    elif message_type == "editor_open":
                        content = message.get('content')
                        file_name = message.get('fileName')
                        file_type = message.get('fileType')

                        if content and file_name and file_type:
                            await _handle_editor_open(
                                db=db,
                                conversation_id=conversation_id,
                                sender=user,
                                file_name=file_name,
                                file_type=file_type,
                                content=content
                            )

                    elif message_type == "editor_change":
                        content = message.get('content')
                        file_name = message.get('fileName')

                        if content and file_name:
                            await _handle_editor_change(
                                db=db,
                                conversation_id=conversation_id,
                                sender=user,
                                file_name=file_name,
                                content=content
                            )

                    elif message_type == "editor_close":
                        file_name = message.get('fileName')

                        if file_name:
                            await _handle_editor_close(
                                db=db,
                                conversation_id=conversation_id,
                                sender=user,
                                file_name=file_name
                            )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for {user.email}")
                connection_active = False
                break
            except asyncio.TimeoutError:
                logger.info(f"Connection timed out for {user.email}")
                connection_active = False
                break
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                logger.error(traceback.format_exc())
                connection_active = False
                break

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        traceback.print_exc()
    finally:
        if ws_connection_id:
            try:
                async with asyncio.timeout(10):
                    await connection_health.disconnect(
                        conversation_id,
                        ws_connection_id,
                        reason="connection closed"
                    )
            except Exception as cleanup_error:
                logger.error(f"Cleanup error: {cleanup_error}")

        try:
            await db.close()
        except Exception as db_error:
            logger.error(f"Database cleanup error: {db_error}")
