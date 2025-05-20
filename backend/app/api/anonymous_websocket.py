# app/routes/anonymous_websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, Optional, Set, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import json
import asyncio
import logging
import traceback
import re
import time
from pydantic import BaseModel, Field, validator
import ipaddress

from app.core.config import settings
from app.services.agents.agent_manager import agent_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Only allow these specific agents for anonymous access
ALLOWED_ANONYMOUS_AGENTS = ["CUSTOMERSERVICE"]

# Security configuration
MAX_ANONYMOUS_CONNECTIONS = 200  # Maximum concurrent anonymous connections
MAX_CONNECTIONS_PER_IP = 3       # Maximum connections per IP address
MAX_MESSAGE_LENGTH = 1000        # Maximum message length in characters
MAX_MESSAGES_PER_MINUTE = 20     # Rate limit for messages per minute
CONNECTION_TIMEOUT = 60          # Timeout for connections in seconds
IP_COOLDOWN_PERIOD = 60          # Cooldown period for IPs that hit rate limits (seconds)

# Store anonymous connections in memory (no persistence)
anonymous_connections: Dict[str, WebSocket] = {}

# Track IP addresses and their connection/message counts
ip_connections: Dict[str, Set[str]] = {}        # IP -> Set of session IDs
ip_message_counts: Dict[str, List[float]] = {}  # IP -> List of message timestamps
ip_cooldowns: Dict[str, float] = {}             # IP -> Cooldown expiry timestamp

# Track total active connections
active_connection_count = 0

# Pydantic model for validating chat messages
class ChatMessage(BaseModel):
    type: str = Field(..., pattern="^message$")  # Only allow "message" type
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    timestamp: Optional[datetime] = None

    @validator('content')
    def validate_content(cls, v):
        # Check for potentially malicious patterns
        if re.search(r'<script|<iframe|javascript:|data:text/html|base64', v, re.IGNORECASE):
            raise ValueError("Content contains potentially unsafe patterns")
        return v

# Dependency to check for IP limits and cooldowns
async def check_ip_limits(websocket: WebSocket) -> str:
    global active_connection_count
    
    # Extract client IP
    client_ip = websocket.client.host
    
    # Check if the IP is in cooldown period
    current_time = time.time()
    if client_ip in ip_cooldowns:
        if current_time < ip_cooldowns[client_ip]:
            cooldown_remaining = int(ip_cooldowns[client_ip] - current_time)
            logger.warning(f"IP {client_ip} is in cooldown for {cooldown_remaining} more seconds")
            await websocket.close(code=4029, reason=f"Rate limit exceeded, try again in {cooldown_remaining} seconds")
            raise HTTPException(status_code=429, detail="Too many requests")
        else:
            # Cooldown expired, remove it
            del ip_cooldowns[client_ip]
    
    # Check global connection limit
    if active_connection_count >= MAX_ANONYMOUS_CONNECTIONS:
        logger.warning(f"Global connection limit reached: {active_connection_count}/{MAX_ANONYMOUS_CONNECTIONS}")
        await websocket.close(code=4029, reason="Server is at capacity, try again later")
        raise HTTPException(status_code=503, detail="Server is at capacity")
    
    # Check connections per IP limit
    if client_ip in ip_connections and len(ip_connections[client_ip]) >= MAX_CONNECTIONS_PER_IP:
        logger.warning(f"IP {client_ip} exceeded connection limit: {len(ip_connections[client_ip])}/{MAX_CONNECTIONS_PER_IP}")
        await websocket.close(code=4029, reason="Connection limit exceeded")
        raise HTTPException(status_code=429, detail="Too many connections from your IP")
    
    return client_ip

# Function to clean up old message timestamps for rate limiting
def clean_old_message_timestamps(ip: str):
    if ip in ip_message_counts:
        # Keep only timestamps from the last minute
        current_time = time.time()
        one_minute_ago = current_time - 60
        ip_message_counts[ip] = [t for t in ip_message_counts[ip] if t > one_minute_ago]

# Check if IP has hit message rate limit
def check_message_rate_limit(ip: str) -> bool:
    clean_old_message_timestamps(ip)
    
    # Count recent messages
    if ip in ip_message_counts:
        if len(ip_message_counts[ip]) >= MAX_MESSAGES_PER_MINUTE:
            # Set a cooldown period for this IP
            ip_cooldowns[ip] = time.time() + IP_COOLDOWN_PERIOD
            logger.warning(f"IP {ip} hit message rate limit and was placed in cooldown for {IP_COOLDOWN_PERIOD} seconds")
            return True
    
    # Add current timestamp to message counts
    if ip not in ip_message_counts:
        ip_message_counts[ip] = []
    
    ip_message_counts[ip].append(time.time())
    return False

async def send_token(websocket: WebSocket, token: str):
    """Send a streaming token to the client."""
    try:
        await websocket.send_json({
            "type": "token",
            "token": token,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error sending token: {e}")

async def send_typing_indicator(websocket: WebSocket, agent_type: str, is_typing: bool):
    """Send typing indicator to the client."""
    try:
        await websocket.send_json({
            "type": "typing_status",
            "identifier": f"{agent_type.lower()}@system.local",
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": agent_type
        })
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")

async def send_error_message(websocket: WebSocket, message: str):
    """Send an error message to the client."""
    try:
        await websocket.send_json({
            "type": "message",
            "content": message,
            "id": str(uuid4()),
            "identifier": "system",
            "is_owner": False,
            "email": "system@system.local",
            "agent_type": "SYSTEM",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

# IMPORTANT: Don't include "/ws" in the route path
# FastAPI will add the prefix we specify in main.py
@router.websocket("/anonymous/{agent_type}")
async def anonymous_websocket_endpoint(
    websocket: WebSocket,
    agent_type: str,
    session_id: str,
    connection_id: Optional[str] = None
):
    global active_connection_count
    
    # Log request details for debugging
    logger.info(f"WebSocket request received for agent: {agent_type}, session: {session_id}")
    
    # Initialize connection tracking
    client_ip = None
    connection_key = None
    
    try:
        # Check IP limits before accepting the connection
        client_ip = await check_ip_limits(websocket)
        
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for agent {agent_type}")
        
        # Normalize agent type and validate
        agent_type = agent_type.upper()
        if agent_type not in ALLOWED_ANONYMOUS_AGENTS:
            logger.warning(f"Attempted access to unauthorized agent: {agent_type}")
            await send_error_message(
                websocket, 
                f"Sorry, {agent_type} is not available for anonymous chat. Available agents: {', '.join(ALLOWED_ANONYMOUS_AGENTS)}"
            )
            await websocket.close(code=4003, reason=f"Agent {agent_type} not available for anonymous access")
            return
        
        # Validate and sanitize session_id (prevent injection)
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            logger.warning(f"Invalid session_id format: {session_id}")
            await websocket.close(code=4003, reason="Invalid session ID format")
            return
            
        # Generate a connection ID if not provided
        if not connection_id:
            connection_id = str(uuid4())
        else:
            # Validate connection_id format
            if not re.match(r'^[a-zA-Z0-9_-]+$', connection_id):
                logger.warning(f"Invalid connection_id format: {connection_id}")
                await websocket.close(code=4003, reason="Invalid connection ID format")
                return
        
        connection_key = f"{session_id}:{connection_id}"
        
        # Store the connection
        anonymous_connections[connection_key] = websocket
        
        # Track IP connections
        if client_ip not in ip_connections:
            ip_connections[client_ip] = set()
        ip_connections[client_ip].add(connection_key)
        
        # Increment active connection count
        active_connection_count += 1
        
        # Set up a virtual thread ID for this anonymous session
        # This is needed for the agent_manager but won't be persisted
        virtual_thread_id = f"anonymous-{session_id}"
        
        logger.info(f"Anonymous WebSocket connected: {agent_type} / {session_id} / {client_ip}")
        
        # Message handling loop
        while True:
            try:
                # Receive message with timeout to prevent hanging connections
                message_json = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=CONNECTION_TIMEOUT
                )
                
                logger.info(f"Received message from client: {message_json}")
                
                # Check message rate limits
                if check_message_rate_limit(client_ip):
                    await send_error_message(
                        websocket,
                        "You've sent too many messages. Please wait a moment before trying again."
                    )
                    continue
                
                # Validate message structure and content
                try:
                    # Validate message with Pydantic model
                    chat_message = ChatMessage(**message_json)
                    
                    # Extract message content and type
                    message_type = chat_message.type
                    content = chat_message.content
                    
                    if message_type == "message":
                        # First send a typing indicator
                        await send_typing_indicator(websocket, agent_type, True)
                        
                        # Define streaming callback for real-time token updates
                        async def streaming_callback(token: str):
                            if token and token.strip():
                                await send_token(websocket, token)
                                # Mark that we've sent tokens
                                streaming_callback.tokens_sent = True
                        
                        # Initialize the token tracking attribute
                        streaming_callback.tokens_sent = False
                        
                        try:
                            # Process with agent_manager
                            # We're using only the specified agent type
                            response_agent, response = await agent_manager.process_conversation(
                                message=content,
                                conversation_agents=[agent_type],
                                agents_config={agent_type: "Anonymous session"},
                                mention=agent_type,  # Force this specific agent
                                thread_id=virtual_thread_id,
                                response_callback=streaming_callback
                            )
                            
                            # Clear typing indicator
                            await send_typing_indicator(websocket, agent_type, False)
                            
                            # If we're using streaming tokens, we don't need to send the full response again
                            # Only send the full response if we didn't stream tokens
                            if not hasattr(streaming_callback, 'tokens_sent') or not streaming_callback.tokens_sent:
                                # Send the full response
                                await websocket.send_json({
                                    "type": "message",
                                    "content": response,
                                    "id": str(uuid4()),
                                    "identifier": f"{agent_type.lower()}@system.local",
                                    "is_owner": False,
                                    "email": f"{agent_type.lower()}@system.local",
                                    "agent_type": agent_type,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            
                        except Exception as e:
                            logger.error(f"Error processing agent response: {e}")
                            logger.error(traceback.format_exc())
                            
                            # Clear typing indicator
                            await send_typing_indicator(websocket, agent_type, False)
                            
                            # Send error message
                            await send_error_message(
                                websocket,
                                "I'm sorry, there was an error processing your message. Please try again."
                            )
                            
                except ValueError as validation_error:
                    logger.warning(f"Invalid message format: {validation_error}")
                    await send_error_message(
                        websocket,
                        "Your message couldn't be processed. Please make sure it's under 1000 characters and doesn't contain potentially unsafe content."
                    )
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {agent_type} / {session_id}")
                break
                
            except asyncio.TimeoutError:
                logger.info(f"WebSocket timeout: {agent_type} / {session_id}")
                # Send a ping to check if connection is still alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    # Connection is likely dead, break the loop
                    break
                
            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {e}")
                logger.error(traceback.format_exc())
                break
                
    except HTTPException:
        # HTTP exceptions are already handled, just pass
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        logger.error(traceback.format_exc())
        
    finally:
        # Clean up the connection
        if connection_key and connection_key in anonymous_connections:
            anonymous_connections.pop(connection_key, None)
            
            # Decrement active connection count
            active_connection_count -= 1
            
            # Remove from IP tracking
            if client_ip and client_ip in ip_connections:
                ip_connections[client_ip].discard(connection_key)
                if not ip_connections[client_ip]:
                    # No more connections from this IP, remove the entry
                    ip_connections.pop(client_ip, None)
        
        # Close the WebSocket if it's still open
        try:
            await websocket.close()
        except:
            pass
        
        logger.info(f"Anonymous WebSocket connection cleaned up: {agent_type} / {session_id}")
