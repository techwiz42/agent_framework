"""
Telephony WebSocket endpoint using Deepgram Voice Agent API
Bridges Twilio MediaStream with Deepgram's conversational AI
"""

import asyncio
import json
import base64
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging
import re

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from twilio.rest import Client as TwilioClient
from agents import WebSearchTool

from app.models.models import PhoneCall, CallDirection, CallMessage, Conversation, Message
from app.db.database import get_db
from app.services.voice.deepgram_voice_agent import get_voice_agent_service, VoiceAgentSession
from app.core.config import settings
from app.services.voice.voice_agent_collaboration import voice_agent_collaboration_service
from app.services.usage_service import usage_service
from app.models.models import TelephonyConfiguration
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
# from app.api.telephony_status import TelephonyStatusManager  # TODO: Implement or remove

logger = logging.getLogger(__name__)

def count_words(text: str) -> int:
    """Count words in text for usage tracking"""
    if not text or not text.strip():
        return 0
    return len(text.split())

def sanitize_phone_number(phone: str) -> str:
    """Enhanced phone number sanitization against injection attacks"""
    if not phone:
        return "UNKNOWN"
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Validate format (+ followed by 10-15 digits)
    if not re.match(r'^\+\d{10,15}$', cleaned):
        logger.warning(f"Invalid phone number format, sanitized to UNKNOWN: {phone}")
        return "UNKNOWN"
    
    # Additional security check: ensure no injection patterns
    from app.security.prompt_injection_filter import prompt_filter
    risk_score = prompt_filter.calculate_risk_score(phone)
    if risk_score > 0.3:  # Suspicious phone number format
        logger.warning(f"Suspicious phone number blocked: {phone}")
        return "UNKNOWN"
    
    return cleaned

def sanitize_organization_data(data: str, field_name: str = "organization_data") -> str:
    """Sanitize organization-provided data for safe use in system prompts"""
    if not data:
        return ""
    
    from app.security.prompt_injection_filter import prompt_filter
    
    # Use the organization data validator which is more restrictive
    sanitized = prompt_filter.validate_organization_data(data)
    
    if sanitized != data:
        logger.warning(f"Organization {field_name} was sanitized: original length {len(data)}, sanitized length {len(sanitized)}")
    
    return sanitized

def extract_agent_name_secure(custom_prompt: str) -> Optional[str]:
    """Securely extract agent name from custom instructions with validation"""
    if not custom_prompt:
        return None
    
    # First sanitize the input
    safe_prompt = sanitize_organization_data(custom_prompt, "agent_name_extraction")
    
    # Look for common patterns that indicate an agent name
    patterns = [
        r"(?:I'm|I am|My name is)\s+([A-Z][a-zA-Z]+)(?:,|\s|$)",
        r"(?:Your name is)\s+([A-Z][a-zA-Z]+)(?:,|\s|\.|\n|$)",
        r"(?:You are)\s+([A-Z][a-zA-Z]+)(?:,|\s|$)",
        r"(?:This is)\s+([A-Z][a-zA-Z]+)(?:,|\s|$)",
        r"(?:Call me)\s+([A-Z][a-zA-Z]+)(?:,|\s|\.|\n|$)",
        r"([A-Z][a-zA-Z]+)\s+(?:is your name)",
        r"(?:You're called|You are called)\s+([A-Z][a-zA-Z]+)",
        r"(?:Hi,? I am)\s+([A-Z][a-zA-Z]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, safe_prompt)
        if match:
            name = match.group(1)
            
            # Security validation of extracted name
            if len(name) > 20:  # Reject overly long names
                continue
                
            # Validate the name isn't a common word or potential injection
            common_words = ['AI', 'Assistant', 'Agent', 'Your', 'The', 'This', 'An', 'A', 
                          'Ignore', 'System', 'Admin', 'Root', 'Override', 'Execute',
                          'Script', 'Function', 'Command', 'Prompt', 'Instruction']
            
            if name not in common_words:
                # Additional security check on the extracted name
                from app.security.prompt_injection_filter import prompt_filter
                name_risk = prompt_filter.calculate_risk_score(name)
                if name_risk < 0.2:  # Low risk names only
                    return name
                else:
                    logger.warning(f"Potentially malicious agent name rejected: {name} (risk: {name_risk:.2f})")
    
    return None


class TelephonyVoiceAgentHandler:
    """Handles telephony connections using Deepgram Voice Agent"""
    
    def __init__(self):
        self.voice_agent_service = get_voice_agent_service()
        self.call_sessions: Dict[str, Dict[str, Any]] = {}
        self.db_locks: Dict[str, asyncio.Lock] = {}  # Per-session database locks
        
        # Initialize web search tool
        self.web_search_tool = WebSearchTool(search_context_size="medium")
        
        # Rate limiting settings
        self.max_concurrent_connections = 50  # Maximum concurrent WebSocket connections
        self.max_audio_packets_per_second = 100  # Maximum audio packets per second per session
        self.connection_count = 0
        self.session_packet_counts: Dict[str, int] = {}  # Track packet counts per session
        self.packet_reset_task: Optional[asyncio.Task] = None
        
    async def handle_connection(self, websocket: WebSocket, db: AsyncSession):
        """Handle incoming Twilio WebSocket connection"""
        session_id = None
        voice_session: Optional[VoiceAgentSession] = None
        flush_task = None
        
        try:
            # Rate limiting: Check concurrent connections
            if self.connection_count >= self.max_concurrent_connections:
                logger.warning(f"🚫 Rate limit exceeded: {self.connection_count} concurrent connections")
                await websocket.close(code=1008, reason="Rate limit exceeded")
                return
            
            await websocket.accept()
            self.connection_count += 1
            logger.info(f"🔌 Accepted new telephony Voice Agent connection ({self.connection_count}/{self.max_concurrent_connections})")
            
            # Start packet reset task if not already running
            if self.packet_reset_task is None or self.packet_reset_task.done():
                self.packet_reset_task = asyncio.create_task(self._reset_packet_counts_periodically())
            
            # Process Twilio messages
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                event_type = data.get("event")
                
                if event_type == "start":
                    # Initialize session
                    session_id = await self._handle_start(data, db)
                    
                    # Create Voice Agent session
                    session_info = self.call_sessions[session_id]
                    try:
                        voice_session = await self._create_voice_agent_session(
                            session_id, 
                            session_info
                        )
                        logger.info(f"✅ Voice Agent session created successfully")
                    except Exception as e:
                        logger.error(f"❌ Voice Agent session creation failed: {e}")
                        logger.error("📞 Voice Agent not available - calls will still work but without advanced features")
                        # Continue without Voice Agent - basic call handling still works
                        voice_session = None
                    
                    # Register handlers only if Voice Agent session was created
                    if voice_session:
                        self._setup_event_handlers(
                            voice_session, 
                            session_id, 
                            websocket,
                            db
                        )
                        
                        # Send custom greeting with organization name
                        await self._send_custom_greeting(voice_session, session_info)
                        
                        # Start periodic flush task to reduce latency
                        flush_task = asyncio.create_task(
                            self._periodic_flush_task(session_id, db)
                        )
                    else:
                        logger.info("📞 Continuing without Voice Agent - call will timeout gracefully")
                    
                elif event_type == "media":
                    # Forward audio to Voice Agent
                    if voice_session:
                        await self._handle_media(data, voice_session)
                        
                elif event_type == "stop":
                    logger.info("📞 Call ended by Twilio")
                    break
                    
        except WebSocketDisconnect:
            logger.info("📞 Twilio WebSocket disconnected")
        except Exception as e:
            logger.error(f"❌ Error in Voice Agent handler: {e}")
        finally:
            # Cancel periodic flush task
            if flush_task:
                flush_task.cancel()
                try:
                    await flush_task
                except asyncio.CancelledError:
                    pass
                    
            # Cleanup connection count and session
            self.connection_count = max(0, self.connection_count - 1)
            if session_id:
                self.session_packet_counts.pop(session_id, None)
                await self._cleanup_session(session_id, db)
            
            logger.info(f"🔌 Connection closed ({self.connection_count}/{self.max_concurrent_connections})")
            if voice_session:
                await self.voice_agent_service.end_session(session_id)
    
    async def _reset_packet_counts_periodically(self):
        """Reset packet counts every second for rate limiting"""
        while True:
            try:
                await asyncio.sleep(1)  # Reset every second
                self.session_packet_counts.clear()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error resetting packet counts: {e}")
    
    async def _handle_start(self, data: Dict[str, Any], db: AsyncSession) -> str:
        """Handle Twilio start event"""
        stream_data = data.get("start", {})
        stream_sid = stream_data.get("streamSid", "")
        custom_params = stream_data.get("customParameters", {})
        
        # Extract call info
        call_sid = custom_params.get("call_sid", "")
        from_number = custom_params.get("from", "Unknown")
        to_number = custom_params.get("to", "Unknown")
        org_phone = custom_params.get("org_phone", to_number)  # Use org_phone if available, fallback to to_number
        tenant_id = custom_params.get("tenant_id")
        
        logger.info(f"📞 New call: {sanitize_phone_number(from_number)} → {sanitize_phone_number(to_number)} (org: {sanitize_phone_number(org_phone)})")
        
        # Get telephony configuration by organization phone number with tenant info
        config_query = select(TelephonyConfiguration).options(
            selectinload(TelephonyConfiguration.tenant)
        ).where(
            TelephonyConfiguration.organization_phone_number == org_phone
        )
        config_result = await db.execute(config_query)
        config = config_result.scalar_one_or_none()
        
        if not config:
            logger.error(f"❌ No telephony config found for {to_number}")
            raise Exception("No telephony configuration found")
        
        # Get existing phone call record (created by webhook handler)
        phone_call_query = select(PhoneCall).where(PhoneCall.call_sid == call_sid)
        phone_call_result = await db.execute(phone_call_query)
        phone_call = phone_call_result.scalar_one_or_none()
        
        if not phone_call:
            # Fallback: create phone call record if it doesn't exist
            phone_call = PhoneCall(
                telephony_config_id=config.id,
                call_sid=call_sid,
                customer_phone_number=from_number,
                organization_phone_number=org_phone,
                platform_phone_number=to_number,
                direction=CallDirection.INBOUND.value,
                status="in-progress",
                start_time=datetime.utcnow()
            )
            db.add(phone_call)
            await db.commit()
            await db.refresh(phone_call)
        else:
            logger.info(f"📞 Using existing phone call record: {phone_call.id}")
        
        # Create conversation
        conversation = await self._create_call_conversation(db, phone_call, config)
        
        # Store session info
        session_id = stream_sid
        self.call_sessions[session_id] = {
            "stream_sid": stream_sid,
            "call_sid": call_sid,
            "phone_call": phone_call,
            "conversation": conversation,
            "config": config,
            "from_number": from_number,
            "to_number": to_number,
            "start_time": datetime.utcnow(),
            "pending_messages": [],  # Initialize pending messages list
            "transfer_pending": False,  # Track if agent asked about transfer
            "transfer_question_time": None,  # When the transfer question was asked
            "collaboration_pending": False,  # Track if system offered collaboration
            "collaboration_question_time": None,  # When collaboration was offered
            "collaboration_user_message": None  # Store the user message that triggered collaboration offer
        }
        
        # Initialize database lock for this session
        self.db_locks[session_id] = asyncio.Lock()
        
        # TODO: Update telephony status
        # status_manager = TelephonyStatusManager()
        # await status_manager.add_active_call(
        #     tenant_id=str(config.tenant_id),
        #     call_sid=call_sid,
        #     from_number=from_number,
        #     start_time=datetime.utcnow()
        # )
        
        logger.info(f"✅ Session initialized: {session_id}")
        return session_id
    
    async def _create_voice_agent_session(
        self, 
        session_id: str, 
        session_info: Dict[str, Any]
    ) -> VoiceAgentSession:
        """Create and configure Voice Agent session"""
        config = session_info["config"]
        
        # Build system prompt
        system_prompt = self._build_system_prompt(config, session_info)
        
        # Create Voice Agent session
        voice_session = await self.voice_agent_service.create_session(
            session_id=session_id,
            system_prompt=system_prompt,
            voice_model=config.voice_id or "aura-2-thalia-en"
        )
        
        return voice_session
    
    def _extract_agent_name(self, custom_prompt: str) -> Optional[str]:
        """SECURE: Extract agent name from custom instructions with validation"""
        # Use the secure version defined at module level
        return extract_agent_name_secure(custom_prompt)

    async def _send_custom_greeting(self, voice_session: VoiceAgentSession, session_info: Dict[str, Any]):
        """SECURE: Send a custom greeting message with sanitized organization name"""
        try:
            config = session_info["config"]
            
            # SECURITY: Get and sanitize organization name from tenant
            org_name = "this organization"  # Default fallback
            if hasattr(config, 'tenant') and config.tenant:
                raw_org_name = config.tenant.name or "this organization"
                org_name = sanitize_organization_data(raw_org_name, "greeting_org_name")
                if not org_name.strip():  # If sanitization removed everything, use fallback
                    org_name = "this organization"
            
            # SECURITY: Extract agent name using secure method
            agent_name = None
            if hasattr(config, 'tenant') and config.tenant and config.tenant.description:
                agent_name = self._extract_agent_name(config.tenant.description)
            
            # Create the actual greeting message that will be spoken
            if agent_name:
                greeting_message = f"Hello! Thank you for calling {org_name}. This is {agent_name}, your AI assistant. How can I help you today?"
            else:
                greeting_message = f"Hello! Thank you for calling {org_name}. This is your AI assistant. How can I help you today?"
            
            # Send the actual greeting message
            await voice_session.send_greeting_message(greeting_message)
            
            logger.info(f"📞 Sent custom greeting message for {org_name}" + (f" with agent name {agent_name}" if agent_name else ""))
            
        except Exception as e:
            logger.error(f"❌ Failed to send custom greeting: {e}")
            # Fallback to generic greeting
            await voice_session.send_greeting_message("Hello! Thank you for calling. This is your AI assistant. How can I help you today?")
    
    def _build_system_prompt(
        self, 
        config: Any, 
        session_info: Dict[str, Any]
    ) -> str:
        """SECURE: Build system prompt for Voice Agent with input sanitization"""
        from_number = sanitize_phone_number(session_info["from_number"])
        
        # Get organization information from tenant with SECURITY SANITIZATION
        org_info = ""
        contact_info = ""
        additional_instructions = ""
        org_name = "this organization"  # Default fallback
        agent_name = None  # Extract agent name from custom prompt
        
        if hasattr(config, 'tenant') and config.tenant:
            tenant = config.tenant
            
            # SECURITY: Sanitize organization name before use in prompt
            raw_org_name = tenant.name or "this organization"
            org_name = sanitize_organization_data(raw_org_name, "organization_name")
            if not org_name.strip():  # If sanitization removed everything, use fallback
                org_name = "this organization"
            
            org_info = f"Organization: {org_name}"
            
            # SECURITY: Sanitize organization description before use in prompt
            if tenant.description and tenant.description.strip():
                safe_description = sanitize_organization_data(tenant.description, "organization_description")
                if safe_description.strip():  # Only add if sanitization left something useful
                    additional_instructions = f"""
ADDITIONAL INSTRUCTIONS FOR THIS ORGANIZATION:
{safe_description}

Follow these specific instructions in addition to your general role."""
                else:
                    logger.warning("Organization description was completely filtered due to security concerns")
            
            # Build contact person information for call transfers
            contact_parts = []
            if tenant.phone:
                # SECURITY: Sanitize contact phone
                safe_phone = sanitize_phone_number(tenant.phone)
                if safe_phone != "UNKNOWN":
                    contact_parts.append(f"Phone: {safe_phone}")
            if tenant.organization_email:
                # SECURITY: Basic email sanitization
                safe_email = sanitize_organization_data(tenant.organization_email, "organization_email")
                if safe_email.strip() and "@" in safe_email:  # Basic email validation
                    contact_parts.append(f"Email: {safe_email}")
            
            if contact_parts:
                contact_info = f"""
CALL TRANSFER OPTION:
ONLY offer call transfer when the caller explicitly requests to speak with a human person or asks to be connected to a human representative.
DO NOT offer transfer when consulting with AI specialist agents or during collaboration workflows.
Contact Information: {', '.join(contact_parts)}
Say something like: "I can transfer you to a human representative who can help you directly. Would you like me to connect you now?"
"""
        
        # SECURITY: Extract agent name using secure method
        if hasattr(config, 'tenant') and config.tenant and config.tenant.description:
            agent_name = self._extract_agent_name(config.tenant.description)
        
        # Build greeting format based on whether agent name is available
        if agent_name:
            greeting_format = f"Hello! Thank you for calling {org_name}. This is {agent_name}, your AI assistant. How can I help you today?"
        else:
            greeting_format = f"Hello! Thank you for calling {org_name}. This is your AI assistant. How can I help you today?"
        
        prompt = f"""You are an AI assistant answering a phone call for {org_name}.

{org_info}

Caller's phone number: {from_number}

CRITICAL: You must start the conversation immediately with a friendly, professional greeting that INCLUDES the organization name "{org_name}". Do not wait for the caller to speak first.

REQUIRED greeting format: "{greeting_format}"

You MUST say the organization name "{org_name}" in your very first greeting."""

        # Add agent name instructions if available
        if agent_name:
            prompt += f"""
You MUST introduce yourself by name as "{agent_name}" in your greeting and throughout the conversation when appropriate."""

        prompt += f"""

{additional_instructions}

Your role:
- Answer on behalf of {org_name}
- Be helpful, professional, and conversational
- Keep responses concise and natural for phone conversations
- Provide information about the organization when asked
- If you don't know something, acknowledge it honestly and offer alternatives

WEB SEARCH CAPABILITY:
- You have direct access to web search for current information
- When callers ask about news, prices, weather, recent events, or current information, you can search the web instantly
- If a caller asks you to "search the web", "look it up online", or needs current information, you will automatically search and provide results
- Examples: "What's the weather like today?", "Search for recent news about...", "What are current gas prices?"
- You can also consult with other specialist teams when complex questions arise that require human expertise

{contact_info}

Important:
- This is a phone conversation, so avoid long responses
- Speak naturally, as if having a real phone conversation
- Always identify yourself as representing the organization
- Always greet the caller first when the call begins
- You have direct web search access for current information and can consult specialists for complex questions
"""
        
        # Additional instructions are already included above in the ADDITIONAL INSTRUCTIONS section
        
        # Add welcome message if configured
        if config.welcome_message:
            prompt += f"\n\nCustom welcome message to incorporate: {config.welcome_message}"
            prompt += f"\n\nIMPORTANT: Regardless of the custom welcome message, you MUST always include the organization name '{org_name}' in your greeting."
            
        return prompt
    
    def _check_for_transfer_question(self, agent_text: str, session_info: Dict[str, Any]) -> bool:
        """Check if agent is asking about transferring the call"""
        agent_text_lower = agent_text.lower()
        
        # Look for questions about transferring
        transfer_question_phrases = [
            "would you like me to transfer",
            "would you like to be transferred",
            "shall i transfer you",
            "should i transfer you", 
            "would you like to speak with",
            "would you like me to connect you",
            "shall i connect you",
            "should i connect you",
            "would you like me to connect you now",
            "can i transfer you",
            "can i connect you",
            "shall i put you through",
            "would you like to be connected"
        ]
        
        return any(phrase in agent_text_lower for phrase in transfer_question_phrases)
    
    def _check_for_transfer_consent(self, user_text: str, session_info: Dict[str, Any]) -> bool:
        """Check if user is agreeing to be transferred"""
        user_text_lower = user_text.lower().strip()
        
        # Positive responses indicating consent
        positive_responses = [
            "yes", "yeah", "yep", "sure", "okay", "ok", "alright", "please",
            "yes please", "that would be great", "that sounds good", 
            "i would like that", "transfer me", "connect me"
        ]
        
        # Negative responses
        negative_responses = [
            "no", "nah", "not now", "not yet", "maybe later", "i'm good",
            "that's okay", "no thanks", "no thank you"
        ]
        
        # Check for explicit positive consent
        is_positive = any(response in user_text_lower for response in positive_responses)
        is_negative = any(response in user_text_lower for response in negative_responses)
        
        # Only transfer on clear positive consent, not on negative or unclear responses
        return is_positive and not is_negative
    
    def _check_for_collaboration_consent(self, user_text: str, session_info: Dict[str, Any]) -> bool:
        """Check if user is agreeing to collaboration with expert agents"""
        user_text_lower = user_text.lower().strip()
        
        # Positive responses indicating consent for expert consultation
        basic_positive = ["yes", "yeah", "yep", "sure", "okay", "ok", "alright", "please"]
        expert_positive = [
            "yes please", "that would be great", "that sounds good", 
            "i would like that", "check with", "consult", "ask the experts",
            "get expert help", "talk to specialists", "expert", "specialist"
        ]
        
        # Negative responses
        negative_responses = [
            "no", "nah", "not now", "not yet", "maybe later", "i'm good",
            "that's okay", "no thanks", "no thank you", "just you",
            "keep it simple", "you can handle it"
        ]
        
        # Check for explicit positive consent (prioritize expert-specific language)
        has_expert_language = any(response in user_text_lower for response in expert_positive)
        has_basic_positive = any(response in user_text_lower for response in basic_positive)
        is_negative = any(response in user_text_lower for response in negative_responses)
        
        # Only proceed with collaboration on clear positive consent, especially if expert language is used
        return (has_expert_language or has_basic_positive) and not is_negative
    
    def _check_for_collaboration_request(self, user_text: str, session_info: Dict[str, Any]) -> bool:
        """Check if user is directly requesting collaboration with expert agents"""
        user_text_lower = user_text.lower()
        
        # Direct collaboration request phrases
        collaboration_request_phrases = [
            "can you check with",
            "ask your team",
            "consult with",
            "get expert",
            "talk to specialist",
            "connect me with expert",
            "speak with specialist", 
            "get help from expert",
            "ask the experts",
            "collaborate with",
            "work with other agents",
            "get second opinion",
            "escalate to",
            "need specialist help",
            "expert assistance",
            "specialist consultation",
            "talk to expert",
            "speak to expert", 
            "talk to an expert",
            "speak to an expert",
            "i would like to talk to an expert",
            "i want to talk to an expert",
            "i would like to talk to expert",
            "i want to talk to expert",
            "talk to a specialist",
            "speak to a specialist",
            "i would like to talk to specialist",
            "i want to talk to specialist"
        ]
        
        return any(phrase in user_text_lower for phrase in collaboration_request_phrases)
    
    async def _handle_call_transfer(self, session_id: str, websocket: WebSocket):
        """Handle call transfer to organization contact"""
        session_info = self.call_sessions.get(session_id)
        if not session_info:
            logger.error(f"❌ No session info found for transfer: {session_id}")
            return
            
        config = session_info["config"]
        
        # Get contact phone number from organization
        if hasattr(config, 'tenant') and config.tenant and config.tenant.phone:
            transfer_number = config.tenant.phone
            
            logger.info(f"📞 Transferring call {session_info['call_sid']} to {transfer_number}")
            logger.info(f"🔍 Call SID: {session_info['call_sid']}")
            logger.info(f"🔍 Transfer number: {transfer_number}")
            logger.info(f"🔍 Twilio Account SID: {settings.TWILIO_ACCOUNT_SID}")
            
            try:
                # Use Twilio REST API to transfer the call
                twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                # Create TwiML to transfer the call
                transfer_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Please hold while I transfer your call.</Say>
    <Dial>
        <Number>{transfer_number}</Number>
    </Dial>
</Response>"""
                
                # Update the call with new TwiML
                logger.info(f"🔍 About to send TwiML: {transfer_twiml}")
                call = twilio_client.calls(session_info['call_sid']).update(twiml=transfer_twiml)
                logger.info(f"✅ Call transferred via Twilio API: {session_info['call_sid']} → {transfer_number}")
                logger.info(f"🔍 Twilio API response: {call}")
                
                # Transfer logged via Twilio webhook and cleanup process
                # No direct database logging here to avoid concurrency issues
                
            except Exception as e:
                logger.error(f"❌ Error transferring call: {e}")
                logger.error(f"❌ Call SID: {session_info.get('call_sid', 'unknown')}")
                logger.error(f"❌ Transfer number: {transfer_number}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        else:
            logger.warning(f"⚠️ No contact phone number available for transfer")
    
    async def _delayed_transfer(self, session_id: str, websocket: WebSocket, delay: float = 3.0):
        """Handle call transfer with a delay to let the agent's message finish"""
        try:
            await asyncio.sleep(delay)
            await self._handle_call_transfer(session_id, websocket)
        except Exception as e:
            logger.error(f"❌ Error in delayed transfer: {e}")
    
    def _setup_event_handlers(
        self,
        voice_session: VoiceAgentSession,
        session_id: str,
        websocket: WebSocket,
        db: AsyncSession
    ):
        """Setup event handlers for Voice Agent events"""
        
        # Handler for audio from agent
        async def handle_agent_audio(audio_data: bytes):
            """Send agent's speech to Twilio"""
            # Audio is already in mulaw format from Voice Agent
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            media_message = {
                "event": "media",
                "streamSid": session_id,
                "media": {
                    "payload": audio_base64
                }
            }
            
            await websocket.send_text(json.dumps(media_message))
        
        voice_session.register_audio_handler(handle_agent_audio)
        
        # Handler for conversation text
        async def handle_conversation_text(event: Dict[str, Any]):
            """Save conversation messages as CallMessage objects with security filtering"""
            logger.info(f"🔍 handle_conversation_text called with event: {event}")
            
            # Try both 'content' and 'text' fields (different events may use different field names)
            text = event.get("content", "") or event.get("text", "")
            role = event.get("role", "")
            
            logger.info(f"🔍 Extracted - text: '{text}', role: '{role}'")
            
            if not text:
                logger.warning(f"🔍 Empty text in conversation event, skipping save")
                return
            
            # Apply security filtering based on role
            filtered_text = text
            security_metadata = {}
            
            try:
                from app.security.content_security_pipeline import security_pipeline
                
                context = {
                    "conversation_type": "telephony",
                    "session_id": session_id,
                    "call_id": call_id
                }
                
                is_user = role.lower() in ["user", "human", "customer", "caller"]
                is_agent = role.lower() in ["assistant", "agent", "ai"]
                
                if is_user:
                    # Filter user input
                    filtered_text, security_metadata = await security_pipeline.filter_user_input(
                        text, context
                    )
                    
                    # Log security events if any
                    if security_metadata.get("security_events"):
                        logger.warning(f"🔒 Security events for telephony user input: {security_metadata['security_events']}")
                        
                elif is_agent:
                    # Filter AI response
                    filtered_text, security_metadata = await security_pipeline.filter_ai_response(
                        text, context
                    )
                    
                    # Log if response was filtered
                    if security_metadata.get("filtered"):
                        logger.warning(f"🔒 AI response filtered for security: {security_metadata.get('reason', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Security filtering error: {e}")
                # Continue with original text if filtering fails
                filtered_text = text

            # Handle collaboration workflow for user messages (use original text for consent detection)
            is_user = role.lower() in ["user", "human", "customer", "caller"]
            if is_user and filtered_text.strip():
                try:
                    # Check if user is responding to a collaboration offer
                    session_info = self.call_sessions.get(session_id)
                    if session_info and session_info.get("collaboration_pending", False):
                        if self._check_for_collaboration_consent(text, session_info):
                            logger.info(f"✅ User consented to collaboration: {text[:50]}...")
                            # User agreed - proceed with collaboration using stored message
                            stored_message = session_info.get("collaboration_user_message")
                            if stored_message:
                                from app.services.voice.voice_agent_collaboration import voice_agent_collaboration_service
                                collaboration_initiated = await voice_agent_collaboration_service.process_user_message(
                                    session_id=session_id,
                                    voice_session=voice_session,
                                    user_message=stored_message,
                                    db_session=db,
                                    owner_id=None
                                )
                                if collaboration_initiated:
                                    logger.info(f"🤝 Collaboration workflow initiated for: {stored_message[:50]}...")
                            # Reset collaboration state
                            session_info["collaboration_pending"] = False
                            session_info["collaboration_question_time"] = None
                            session_info["collaboration_user_message"] = None
                        else:
                            logger.info(f"❌ User declined collaboration: {text[:50]}...")
                            # Reset collaboration state
                            session_info["collaboration_pending"] = False
                            session_info["collaboration_question_time"] = None
                            session_info["collaboration_user_message"] = None
                    else:
                        # Check if user is directly requesting collaboration
                        if self._check_for_collaboration_request(text, session_info):
                            logger.info(f"🤝 Direct collaboration request detected: {text[:50]}...")
                            # User directly requested collaboration - proceed immediately
                            try:
                                from app.services.voice.voice_agent_collaboration import voice_agent_collaboration_service
                                collaboration_initiated = await voice_agent_collaboration_service.process_user_message(
                                    session_id=session_id,
                                    voice_session=voice_session,
                                    user_message=text,
                                    db_session=db,
                                    owner_id=None
                                )
                                if collaboration_initiated:
                                    logger.info(f"🤝 Direct collaboration initiated for: {text[:50]}...")
                            except Exception as direct_collab_error:
                                logger.error(f"❌ Error initiating direct collaboration: {direct_collab_error}")
                        # NOTE: Automatic collaboration offering disabled to prevent redundant prompts
                        # Organization instructions in system prompt will handle when to offer collaboration
                        # This allows for more natural, customized collaboration offers per organization
                    
                except Exception as collab_error:
                    logger.error(f"❌ Error in collaboration workflow: {collab_error}")
                    # Continue with normal processing if collaboration fails
                
            session_info = self.call_sessions.get(session_id)
            if not session_info:
                return
                
            conversation = session_info["conversation"]
            phone_call = session_info["phone_call"]
            
            # Create CallMessage for the call details page
            # Map Deepgram Voice Agent roles to our system
            # Possible user role values: "user", "human", "customer", "caller"
            # Possible agent role values: "assistant", "agent", "bot", "ai"
            is_user = role.lower() in ["user", "human", "customer", "caller"]
            is_agent = role.lower() in ["assistant", "agent", "bot", "ai"]
            
            logger.info(f"🔍 Role mapping - original: '{role}' → is_user: {is_user}, is_agent: {is_agent}")
            
            # If role is unclear, try to infer from event type or content
            if not is_user and not is_agent:
                logger.warning(f"🚨 UNKNOWN ROLE: '{role}' - treating as agent for safety")
                is_user = False
            
            # Handle transfer workflow - but only for phone transfers, not expert collaboration
            # IMPORTANT: Only handle transfer if NOT in collaboration workflow
            if is_agent and self._check_for_transfer_question(text, session_info) and not session_info.get("collaboration_pending", False):
                # Agent is asking about transfer - mark as pending
                session_info["transfer_pending"] = True
                session_info["transfer_question_time"] = datetime.utcnow()
                logger.info(f"📞 Agent asked about transfer: {text[:100]}...")
            
            elif is_user and session_info.get("transfer_pending", False) and not session_info.get("collaboration_pending", False):
                # User responding to transfer question - check if they want phone transfer specifically
                if self._check_for_transfer_consent(text, session_info) and not self._check_for_collaboration_request(text, session_info):
                    logger.info(f"✅ User consented to phone transfer: {text[:50]}...")
                    # Reset transfer state and initiate transfer
                    session_info["transfer_pending"] = False
                    session_info["transfer_question_time"] = None
                    import asyncio
                    asyncio.create_task(self._delayed_transfer(session_id, websocket, delay=1.0))
                else:
                    logger.info(f"❌ User declined phone transfer: {text[:50]}...")
                    # Reset transfer state
                    session_info["transfer_pending"] = False
                    session_info["transfer_question_time"] = None
                
            call_message = CallMessage(
                call_id=phone_call.id,
                content=filtered_text,  # Use filtered content
                sender={
                    "identifier": session_info["from_number"] if is_user else "voice_agent",
                    "type": "customer" if is_user else "agent",
                    "name": "Caller" if is_user else "AI Agent",
                    "phone_number": session_info["from_number"] if is_user else None
                },
                timestamp=datetime.utcnow(),
                message_type="transcript",
                message_metadata={
                    "role": role,
                    "session_id": session_id,
                    "call_sid": session_info["call_sid"],
                    "security_metadata": security_metadata,  # Include security info
                    "original_length": len(text) if text != filtered_text else None
                }
            )
            
            # Also create Message for conversation continuity  
            message = Message(
                conversation_id=conversation.id,
                message_type="text",
                agent_type="voice_agent" if not is_user else None,
                content=filtered_text,  # Use filtered content
                message_metadata={
                    "role": role,
                    "call_sid": session_info["call_sid"],
                    "session_id": session_id,
                    "security_metadata": security_metadata  # Include security info
                }
            )
            
            # Add to pending messages batch (don't commit immediately to reduce latency)
            session_info["pending_messages"].extend([call_message, message])
            
            # Process voice-to-CRM-to-calendar integration for user messages
            if is_user and text.strip():
                try:
                    await self._process_customer_data_extraction(session_id, text, db)
                    await self._process_scheduling_intent(session_id, text, db)
                    
                    # Check if user wants web search and perform it directly
                    if self._should_perform_web_search(text):
                        search_results = await self._perform_web_search(session_id, text)
                        if search_results:
                            # Get the voice session and inject the search results
                            voice_session = self.voice_agent_service.sessions.get(session_id)
                            if voice_session:
                                await voice_session.inject_message(search_results, "assistant")
                                logger.info(f"📡 Injected web search results into voice conversation")
                                
                except Exception as crm_error:
                    logger.error(f"❌ Error in CRM/calendar processing: {crm_error}")
                    # Don't let CRM errors affect the main call flow
            
            # Track usage for STT and TTS
            config = session_info["config"]
            word_count = count_words(text)
            
            # Get the database lock for this session
            db_lock = self.db_locks.get(session_id)
            if db_lock and word_count > 0:
                async with db_lock:
                    if is_user:
                        # User speech = STT usage (Deepgram transcribed user's speech)
                        try:
                            await usage_service.record_usage(
                                db=db,
                                tenant_id=config.tenant_id,
                                user_id=None,  # No specific user for phone calls
                                usage_type="stt_words",
                                amount=word_count,
                                service_provider="deepgram",
                                model_name="nova-3",
                                cost_cents=int((word_count / 1000) * 100),  # $1.00 per 1000 words
                                additional_data={
                                    "call_id": str(phone_call.id),
                                    "call_sid": phone_call.call_sid,
                                    "conversation_id": str(conversation.id)
                                }
                            )
                            logger.info(f"📊 STT usage recorded: {word_count} words for user speech")
                        except Exception as e:
                            logger.error(f"❌ Error recording STT usage: {e}")
                    
                    elif is_agent:
                        # Agent speech = TTS usage (Deepgram generated agent's speech)
                        try:
                            await usage_service.record_usage(
                                db=db,
                                tenant_id=config.tenant_id,
                                user_id=None,  # No specific user for phone calls
                                usage_type="tts_words",
                                amount=word_count,
                                service_provider="deepgram",
                                model_name="aura-2-thalia-en",
                                cost_cents=int((word_count / 1000) * 100),  # $1.00 per 1000 words
                                additional_data={
                                    "call_id": str(phone_call.id),
                                    "call_sid": phone_call.call_sid,
                                    "conversation_id": str(conversation.id)
                                }
                            )
                            logger.info(f"📊 TTS usage recorded: {word_count} words for agent speech")
                        except Exception as e:
                            logger.error(f"❌ Error recording TTS usage: {e}")
            
            # Messages will be flushed periodically by the background task
            # or when the call ends to minimize database contention
            
            logger.info(f"💾 Queued {role} message: {text[:50]}...")
            
            # Transfer handling is now managed in the conversation flow above
        
        # Register handler for multiple possible transcript event types
        voice_session.register_event_handler("ConversationText", handle_conversation_text)
        voice_session.register_event_handler("Transcript", handle_conversation_text)
        voice_session.register_event_handler("TranscriptText", handle_conversation_text)
        voice_session.register_event_handler("UserText", handle_conversation_text)
        voice_session.register_event_handler("AgentText", handle_conversation_text)
        
        # Additional possible event types for user speech
        voice_session.register_event_handler("UserTranscript", handle_conversation_text)
        voice_session.register_event_handler("SpeechTranscript", handle_conversation_text)
        voice_session.register_event_handler("RecognitionResult", handle_conversation_text)
        
        # Handler for user speaking events
        async def handle_user_speaking(event: Dict[str, Any]):
            """Track when user is speaking"""
            logger.info("🗣️ User speaking detected")
            # Could add visual indicators or other logic here
        
        voice_session.register_event_handler("UserStartedSpeaking", handle_user_speaking)
        
        # Catch-all handler for debugging unknown events that might contain user speech
        async def handle_unknown_event(event_type: str, event: Dict[str, Any]):
            """Log all unhandled events to catch user speech in unexpected formats"""
            # Check if this event contains text that might be user speech
            text_content = event.get("content", "") or event.get("text", "") or event.get("transcript", "")
            role = event.get("role", "")
            
            if text_content and text_content.strip():
                logger.info(f"🔍 UNHANDLED EVENT with text: {event_type}")
                logger.info(f"🔍 Text: '{text_content}'")
                logger.info(f"🔍 Role: '{role}'")
                logger.info(f"🔍 Full event: {event}")
                
                # If this looks like user speech, try to save it
                if role.lower() in ["user", "human", "customer", "caller"] or event_type.lower().find("user") != -1:
                    logger.warning(f"🚨 POTENTIAL USER MESSAGE in unhandled event: {event_type}")
                    # Route to conversation handler
                    await handle_conversation_text(event)
        
        # Note: No fallback handler method available, but the Voice Agent service
        # logs all unhandled events in _handle_event method
    
    async def _handle_media(self, data: Dict[str, Any], voice_session: VoiceAgentSession):
        """Handle incoming audio from Twilio"""
        session_id = voice_session.session_id
        
        # Rate limiting: Check audio packet rate
        current_count = self.session_packet_counts.get(session_id, 0)
        if current_count >= self.max_audio_packets_per_second:
            logger.warning(f"🚫 Audio rate limit exceeded for session {session_id}: {current_count} packets/sec")
            return
        
        self.session_packet_counts[session_id] = current_count + 1
        
        media_data = data.get("media", {})
        audio_base64 = media_data.get("payload", "")
        
        if not audio_base64:
            return
        
        # Validate audio data size (Twilio mulaw packets are typically ~160 bytes, max 2KB)
        if len(audio_base64) > 4000:  # Base64 encoded, so ~3KB of raw data
            logger.warning(f"🚫 Audio packet too large: {len(audio_base64)} bytes (max 4000)")
            return
            
        try:
            # Decode mulaw audio from Twilio
            audio_data = base64.b64decode(audio_base64)
            
            # Additional validation on decoded data
            if len(audio_data) > 2048:  # 2KB max for raw mulaw data
                logger.warning(f"🚫 Decoded audio too large: {len(audio_data)} bytes (max 2048)")
                return
            
            # Send to Voice Agent
            await voice_session.agent.send_audio(audio_data)
            
        except Exception as e:
            logger.error(f"❌ Error processing audio data: {e}")
            # Don't re-raise to avoid disconnecting the call for invalid audio
    
    async def _create_call_conversation(
        self,
        db: AsyncSession,
        call: PhoneCall,
        config: Any
    ) -> Conversation:
        """Create a conversation record for the phone call"""
        
        conversation = Conversation(
            tenant_id=config.tenant_id,
            title=f"Phone Call - {call.customer_phone_number}",
            description=f"Incoming call from {call.customer_phone_number} (Voice Agent)",
            status="active"
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        # Link call to conversation
        call.conversation_id = conversation.id
        await db.commit()
        
        return conversation
    
    async def _periodic_flush_task(self, session_id: str, db: AsyncSession):
        """Periodically flush pending messages and check transfer timeouts"""
        while True:
            try:
                await asyncio.sleep(3)  # Check every 3 seconds
                await self._flush_pending_messages(session_id, db)
                
                # Check for transfer timeout (30 seconds without response)
                session_info = self.call_sessions.get(session_id)
                if session_info:
                    # Check transfer timeout
                    if session_info.get("transfer_pending", False):
                        question_time = session_info.get("transfer_question_time")
                        if question_time:
                            time_elapsed = (datetime.utcnow() - question_time).total_seconds()
                            if time_elapsed > 30:  # 30 second timeout
                                logger.info(f"⏰ Transfer request timed out for session {session_id}")
                                session_info["transfer_pending"] = False
                                session_info["transfer_question_time"] = None
                    
                    # Check collaboration timeout (30 seconds without response)
                    if session_info.get("collaboration_pending", False):
                        question_time = session_info.get("collaboration_question_time")
                        if question_time:
                            time_elapsed = (datetime.utcnow() - question_time).total_seconds()
                            if time_elapsed > 30:  # 30 second timeout
                                logger.info(f"⏰ Collaboration offer timed out for session {session_id}")
                                session_info["collaboration_pending"] = False
                                session_info["collaboration_question_time"] = None
                                session_info["collaboration_user_message"] = None
                            
            except asyncio.CancelledError:
                # Final flush before task ends
                await self._flush_pending_messages(session_id, db)
                break
            except Exception as e:
                logger.error(f"❌ Error in periodic flush: {str(e)}")
    
    async def _flush_pending_messages(self, session_id: str, db: AsyncSession):
        """Flush pending messages to database in batch"""
        session_info = self.call_sessions.get(session_id)
        if not session_info or "pending_messages" not in session_info:
            return
            
        # Get the database lock for this session
        db_lock = self.db_locks.get(session_id)
        if not db_lock:
            logger.warning(f"⚠️ No database lock found for session {session_id}")
            return
            
        async with db_lock:
            pending_messages = session_info["pending_messages"]
            if not pending_messages:
                return
                
            try:
                # Add all pending messages to session
                for message in pending_messages:
                    db.add(message)
                
                # Commit all at once
                await db.commit()
                
                # Clear pending messages
                session_info["pending_messages"] = []
                
                logger.info(f"💾 Flushed {len(pending_messages)} messages to database")
                
            except Exception as e:
                logger.error(f"❌ Error flushing messages: {str(e)}")
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ Error during rollback: {str(rollback_error)}")
    
    async def _cleanup_session(self, session_id: str, db: AsyncSession):
        """Cleanup session when call ends"""
        session_info = self.call_sessions.get(session_id)
        if not session_info:
            return
            
        # Get the database lock for this session
        db_lock = self.db_locks.get(session_id)
        if not db_lock:
            logger.warning(f"⚠️ No database lock found for session {session_id} during cleanup")
            db_lock = asyncio.Lock()  # Create a temporary lock if needed
            
        try:
            # Flush any remaining pending messages before cleanup
            await self._flush_pending_messages(session_id, db)
            
            async with db_lock:
                # Update phone call record
                phone_call = session_info["phone_call"]
                from datetime import timezone
                phone_call.end_time = datetime.now(timezone.utc)
                phone_call.status = "completed"
                
                # Calculate duration (ensure both times are timezone-aware)
                start_time = phone_call.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                duration = (phone_call.end_time - start_time).total_seconds()
                phone_call.duration_seconds = int(duration)
                
                # Update conversation status
                conversation = session_info["conversation"]
                conversation.status = "completed"
                
                await db.commit()
                
                # Record call duration usage
                config = session_info["config"]
                if phone_call.duration_seconds and phone_call.duration_seconds > 0:
                    try:
                        # Get STT/TTS word counts for this call from usage records
                        from sqlalchemy import and_, select
                        from app.models.models import UsageRecord
                        usage_query = select(UsageRecord).where(
                            and_(
                                UsageRecord.tenant_id == config.tenant_id,
                                UsageRecord.additional_data.op('->>')('call_id') == str(phone_call.id),
                                UsageRecord.usage_type.in_(['stt_words', 'tts_words'])
                            )
                        )
                        usage_result = await db.execute(usage_query)
                        usage_records = usage_result.scalars().all()
                        
                        # Calculate total words (STT + TTS)
                        total_words = sum(record.amount for record in usage_records)
                        
                        # Calculate cost: $1.00 base + $1.00 per 1000 words
                        cost_cents = 100 + int((total_words / 1000) * 100)
                        
                        # Update the call record with the calculated cost
                        phone_call.cost_cents = cost_cents
                        await db.commit()
                        
                        # Record call duration usage (separate from cost calculation)
                        duration_minutes = phone_call.duration_seconds / 60.0
                        
                        await usage_service.record_usage(
                            db=db,
                            tenant_id=config.tenant_id,
                            usage_type="telephony_minutes",
                            amount=int(duration_minutes),
                            cost_cents=cost_cents,
                            additional_data={
                                "call_id": str(phone_call.id),
                                "call_sid": phone_call.call_sid,
                                "voice_agent_type": "deepgram_integrated"
                            }
                        )
                        logger.info(f"📊 Call usage recorded: {total_words} words, cost: {cost_cents} cents (${cost_cents/100:.2f})")
                    except Exception as e:
                        logger.error(f"❌ Error recording call duration usage: {e}")
                
                # Auto-generate summary for completed call
                try:
                    await self._generate_call_summary(phone_call.id, db)
                except Exception as e:
                    logger.error(f"❌ Error generating summary for call {phone_call.id}: {e}")
            
            # TODO: Update telephony status
            # status_manager = TelephonyStatusManager()
            # await status_manager.remove_active_call(
            #     tenant_id=str(session_info["config"].tenant_id),
            #     call_sid=session_info["call_sid"]
            # )
            
            # Cleanup collaboration session if active
            try:
                await voice_agent_collaboration_service._cleanup_session(session_id)
                logger.info(f"🤝 Cleaned up collaboration session {session_id}")
            except Exception as collab_cleanup_error:
                logger.error(f"❌ Error cleaning up collaboration session: {collab_cleanup_error}")

            # Cleanup session and database lock
            del self.call_sessions[session_id]
            if session_id in self.db_locks:
                del self.db_locks[session_id]
            
            logger.info(f"✅ Cleaned up session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up session: {e}")
    
    def get_collaboration_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get collaboration status for a session"""
        return voice_agent_collaboration_service.get_session_status(session_id)

    async def _generate_call_summary(self, call_id: str, db: AsyncSession):
        """Generate summary for a completed call"""
        
        try:
            from sqlalchemy import and_
            
            # Check if summary already exists
            existing_summary_query = select(CallMessage).where(
                and_(
                    CallMessage.call_id == call_id,
                    CallMessage.message_type == 'summary'
                )
            )
            existing_result = await db.execute(existing_summary_query)
            if existing_result.scalar_one_or_none():
                logger.info(f"📝 Summary already exists for call {call_id}")
                return
            
            # Get transcript messages
            transcript_query = (
                select(CallMessage)
                .where(
                    and_(
                        CallMessage.call_id == call_id,
                        CallMessage.message_type == 'transcript'
                    )
                )
                .order_by(CallMessage.timestamp)
            )
            
            result = await db.execute(transcript_query)
            transcript_messages = result.scalars().all()
            
            if not transcript_messages:
                logger.info(f"📝 No transcript messages found for call {call_id}")
                return
            
            # Get call details
            call_query = select(PhoneCall).where(PhoneCall.id == call_id)
            call_result = await db.execute(call_query)
            call = call_result.scalar_one_or_none()
            
            if not call:
                logger.error(f"❌ Call {call_id} not found")
                return
            
            # Generate AI-powered summary
            duration_info = ""
            if call.duration_seconds:
                minutes = call.duration_seconds // 60
                seconds = call.duration_seconds % 60
                duration_info = f" The call lasted {minutes} minutes and {seconds} seconds."
            
            message_count = len(transcript_messages)
            customer_messages = [m for m in transcript_messages if m.sender.get('type') == 'customer']
            agent_messages = [m for m in transcript_messages if m.sender.get('type') == 'agent']
            
            # Build conversation transcript for AI analysis
            conversation_text = []
            for msg in transcript_messages:
                sender_type = msg.sender.get('type', 'unknown')
                sender_name = 'Customer' if sender_type == 'customer' else 'Agent'
                conversation_text.append(f"{sender_name}: {msg.content}")
            
            full_transcript = "\n".join(conversation_text)
            
            # Generate AI summary if transcript has content
            if full_transcript.strip():
                try:
                    # Initialize OpenAI client
                    client = AsyncOpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        organization=getattr(settings, 'OPENAI_ORG_ID', None)
                    )
                    
                    # Generate summary using OpenAI
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an AI assistant that creates concise, informative summaries of phone conversations. "
                                    "Focus on the main topics discussed, any questions asked, issues raised, and resolutions provided. "
                                    "Keep the summary brief but comprehensive, highlighting the key points of the conversation. "
                                    "Do not include call metadata like duration or timestamps in the summary."
                                )
                            },
                            {
                                "role": "user",
                                "content": f"Please summarize the following phone conversation:\n\n{full_transcript}"
                            }
                        ],
                        temperature=0.3,
                        max_tokens=300
                    )
                    
                    ai_summary = response.choices[0].message.content.strip()
                    
                    # Combine AI summary with metadata
                    summary_content = (
                        f"Call Summary - {call.created_at.strftime('%B %d, %Y at %I:%M %p')}\n\n"
                        f"{ai_summary}\n\n"
                        f"Call Details:{duration_info} {message_count} messages exchanged "
                        f"({len(customer_messages)} from customer, {len(agent_messages)} from agent)."
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error generating AI summary: {e}")
                    # Fall back to basic summary
                    summary_content = (
                        f"Call between customer {call.customer_phone_number} and organization "
                        f"on {call.created_at.strftime('%B %d, %Y at %I:%M %p')}.{duration_info} "
                        f"The conversation included {message_count} messages "
                        f"({len(customer_messages)} from customer, {len(agent_messages)} from agent). "
                        f"Unable to generate AI summary due to an error."
                    )
            else:
                # No transcript content available
                summary_content = (
                    f"Call between customer {call.customer_phone_number} and organization "
                    f"on {call.created_at.strftime('%B %d, %Y at %I:%M %p')}.{duration_info} "
                    f"The conversation included {message_count} messages "
                    f"({len(customer_messages)} from customer, {len(agent_messages)} from agent). "
                    f"No conversation transcript available for summary."
                )
            
            # Create summary message
            summary_message = CallMessage(
                call_id=call_id,
                content=summary_content,
                sender={
                    "identifier": "system",
                    "name": "AI Summarizer",
                    "type": "system"
                },
                timestamp=datetime.utcnow(),
                message_type='summary',
                message_metadata={
                    "is_automated": True,
                    "generation_method": "voice_agent_auto_generated",
                    "message_count": message_count,
                    "customer_message_count": len(customer_messages),
                    "agent_message_count": len(agent_messages)
                }
            )
            
            # Add summary to database
            try:
                db.add(summary_message)
                
                # Also update the phone_call summary field
                call.summary = summary_content
                
                await db.commit()
                logger.info(f"📝 ✅ Auto-generated summary for Voice Agent call {call_id}")
                
            except Exception as commit_error:
                logger.error(f"❌ Error committing summary for call {call_id}: {commit_error}")
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ Error during rollback in summary generation: {rollback_error}")
            
        except Exception as e:
            logger.error(f"❌ Error generating summary for call {call_id}: {e}")
            # Don't re-raise - summary generation is optional

    async def _process_customer_data_extraction(
        self, 
        session_id: str, 
        user_message: str, 
        db: AsyncSession
    ):
        """Process customer data extraction from voice conversation"""
        try:
            session_info = self.call_sessions.get(session_id)
            if not session_info:
                return
            
            config = session_info["config"]
            
            # Get or create accumulated customer data for this session
            if "customer_data" not in session_info:
                session_info["customer_data"] = None
            
            # Extract customer information from the conversation text
            from app.services.voice.customer_extraction import get_customer_extraction_service
            extraction_service = get_customer_extraction_service()
            
            # Extract new customer data
            new_data = await extraction_service.extract_customer_data(
                conversation_text=user_message,
                existing_data=session_info["customer_data"]
            )
            
            # Update session with new data
            session_info["customer_data"] = new_data
            
            # Check if we have enough data to create/update a contact
            if new_data.is_sufficient_for_contact():
                # Try to find existing contact
                existing_contact = await extraction_service.find_existing_contact(
                    db, config.tenant_id, new_data
                )
                
                if existing_contact:
                    # Update existing contact with new data
                    updated_contact = await extraction_service.update_contact_from_data(
                        db, existing_contact, new_data
                    )
                    session_info["contact_id"] = updated_contact.id
                    logger.info(f"📞 Updated existing contact {updated_contact.id} from voice data")
                else:
                    # Create new contact from extracted data
                    new_contact = await extraction_service.create_contact_from_data(
                        db, config.tenant_id, config.tenant_id, new_data  # Using tenant_id as user_id for now
                    )
                    if new_contact:
                        session_info["contact_id"] = new_contact.id
                        logger.info(f"📞 Created new contact {new_contact.id} from voice data")
            
        except Exception as e:
            logger.error(f"❌ Error in customer data extraction: {e}")
    
    async def _process_scheduling_intent(
        self,
        session_id: str,
        user_message: str,
        db: AsyncSession
    ):
        """Process scheduling intent detection and calendar operations"""
        try:
            session_info = self.call_sessions.get(session_id)
            if not session_info:
                return
            
            config = session_info["config"]
            
            # Get or create accumulated scheduling preferences for this session
            if "scheduling_preferences" not in session_info:
                session_info["scheduling_preferences"] = None
            
            # Detect scheduling intent and extract preferences
            from app.services.voice.scheduling_intent import get_scheduling_intent_service
            intent_service = get_scheduling_intent_service()
            
            # Extract scheduling preferences
            new_preferences = await intent_service.extract_scheduling_preferences(
                conversation_text=user_message,
                existing_preferences=session_info["scheduling_preferences"]
            )
            
            # Update session with new preferences
            session_info["scheduling_preferences"] = new_preferences
            
            # Handle scheduling intent
            if new_preferences.has_scheduling_intent():
                from app.services.voice.voice_calendar import get_voice_calendar_service
                calendar_service = get_voice_calendar_service()
                
                # For now, use the tenant_id as user_id for calendar operations
                # In a real implementation, you'd determine which staff member's calendar to check
                calendar_user_id = config.tenant_id
                
                if new_preferences.intent.value == "schedule_appointment":
                    # Check availability
                    availability = await calendar_service.check_availability(
                        db, config.tenant_id, calendar_user_id, new_preferences
                    )
                    
                    if availability.has_availability():
                        # Store availability for potential booking
                        session_info["last_availability_check"] = availability
                        
                        # Generate natural language response about availability
                        availability_response = calendar_service.format_availability_for_voice(availability)
                        
                        # Inject availability information into the voice agent
                        voice_session = self.voice_agent_service.sessions.get(session_id)
                        if voice_session:
                            enhanced_instructions = f"""
You just checked the calendar and found available appointment times. 
Respond naturally to the customer with this availability information:

{availability_response}

If they confirm a specific time, you can proceed to book it for them.
"""
                            await voice_session.update_instructions(enhanced_instructions)
                            logger.info(f"📅 Updated voice agent with availability information")
                    else:
                        # No availability found
                        voice_session = self.voice_agent_service.sessions.get(session_id)
                        if voice_session:
                            no_availability_instructions = """
You checked the calendar but didn't find any available times that match their preferences. 
Apologize and offer to:
1. Check different time periods
2. Add them to a waitlist
3. Schedule outside normal business hours
4. Connect them with someone who can manually coordinate scheduling
"""
                            await voice_session.update_instructions(no_availability_instructions)
                            logger.info(f"📅 No availability found, updated voice agent instructions")
                
                elif new_preferences.intent.value == "check_availability":
                    # Just checking availability, not booking yet
                    availability = await calendar_service.check_availability(
                        db, config.tenant_id, calendar_user_id, new_preferences
                    )
                    
                    if availability.has_availability():
                        availability_response = calendar_service.format_availability_for_voice(availability)
                        voice_session = self.voice_agent_service.sessions.get(session_id)
                        if voice_session:
                            await voice_session.inject_message(availability_response, "assistant")
                
                # Handle appointment booking confirmation
                elif new_preferences.intent.value == "schedule_appointment" and session_info.get("last_availability_check"):
                    # Check if user has confirmed a specific time
                    if new_preferences.is_time_specific():
                        availability = session_info["last_availability_check"]
                        best_slots = availability.get_best_slots(1)
                        
                        if best_slots:
                            # Book the appointment
                            contact_id = session_info.get("contact_id")
                            customer_notes = f"Scheduled via voice call. Customer message: {user_message[:200]}"
                            
                            booked_event = await calendar_service.book_appointment(
                                db, config.tenant_id, calendar_user_id, contact_id,
                                best_slots[0], new_preferences, customer_notes
                            )
                            
                            if booked_event:
                                # Update phone call with linked event
                                phone_call = session_info["phone_call"]
                                if phone_call.call_metadata is None:
                                    phone_call.call_metadata = {}
                                phone_call.call_metadata["booked_appointment_id"] = str(booked_event.id)
                                await db.commit()
                                
                                # Confirm booking with customer
                                confirmation_message = calendar_service.format_booking_confirmation(booked_event)
                                voice_session = self.voice_agent_service.sessions.get(session_id)
                                if voice_session:
                                    await voice_session.inject_message(confirmation_message, "assistant")
                                
                                logger.info(f"📅 ✅ Booked appointment {booked_event.id} via voice call")
                            else:
                                # Booking failed
                                voice_session = self.voice_agent_service.sessions.get(session_id)
                                if voice_session:
                                    error_message = "I apologize, but I wasn't able to book that appointment. The time slot may no longer be available. Let me check for other options."
                                    await voice_session.inject_message(error_message, "assistant")
                
                logger.info(f"📅 Processed scheduling intent: {new_preferences.intent.value}")
            
        except Exception as e:
            logger.error(f"❌ Error in scheduling intent processing: {e}")

    async def _perform_web_search(self, session_id: str, user_message: str) -> Optional[str]:
        """Perform web search and return formatted results"""
        try:
            session_info = self.call_sessions.get(session_id)
            if not session_info:
                return None
            
            # Extract search query from user message
            search_query = self._extract_search_query(user_message)
            if not search_query:
                return None
            
            logger.info(f"📡 Performing web search for: {search_query}")
            
            # Perform web search using the tool
            search_results = await self.web_search_tool.web_search(search_query)
            
            if not search_results:
                return "I wasn't able to find any current information on that topic. Would you like me to help you with something else?"
            
            # Format results for voice conversation
            formatted_results = self._format_search_results_for_voice(search_results, search_query)
            
            logger.info(f"📡 Web search completed for: {search_query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error performing web search: {e}")
            return "I encountered an error while searching. Let me try to help you with the information I have available."
    
    def _extract_search_query(self, user_message: str) -> Optional[str]:
        """Extract search query from user message"""
        # Simple extraction - in a real implementation, this could be more sophisticated
        message_lower = user_message.lower()
        
        # Remove web search trigger phrases to get the actual query
        trigger_phrases = [
            "search the web for", "search online for", "look up", "google", 
            "find information about", "search for", "what is", "what are",
            "tell me about", "can you find", "look for"
        ]
        
        query = user_message.strip()
        for phrase in trigger_phrases:
            if phrase in message_lower:
                # Find the phrase and extract everything after it
                phrase_index = message_lower.find(phrase)
                if phrase_index != -1:
                    query = user_message[phrase_index + len(phrase):].strip()
                    break
        
        # Clean up common question words at the beginning
        query = re.sub(r'^(what|who|where|when|why|how|is|are|can|do|does)\s+', '', query, flags=re.IGNORECASE)
        
        return query if query and len(query) > 2 else None
    
    def _format_search_results_for_voice(self, results: List[Dict], query: str) -> str:
        """Format search results for natural voice conversation"""
        if not results:
            return f"I couldn't find current information about {query}."
        
        # Take the most relevant results (usually first 2-3)
        top_results = results[:3]
        
        response_parts = [f"I found some current information about {query}:"]
        
        for i, result in enumerate(top_results, 1):
            title = result.get('title', 'Unknown source')
            content = result.get('content', '')
            
            # Truncate content for voice conversation
            if len(content) > 200:
                content = content[:200] + "..."
            
            if i == 1:
                response_parts.append(f"According to {title}: {content}")
            else:
                response_parts.append(f"Additionally, {title} reports: {content}")
        
        # Add a natural ending
        if len(top_results) > 1:
            response_parts.append("Would you like me to search for more specific information about any of these points?")
        
        return " ".join(response_parts)
    
    def _should_perform_web_search(self, user_message: str) -> bool:
        """Check if user message indicates a web search is needed"""
        message_lower = user_message.lower()
        
        # Direct web search requests
        web_search_indicators = [
            "search the web", "search online", "search the internet",
            "look it up online", "google it", "find information online",
            "check online", "what does the internet say", "search for",
            "current information", "latest news", "recent updates",
            "what's happening", "current events", "up to date",
            "recent", "today", "this week", "this month"
        ]
        
        # Current information topics
        current_info_topics = [
            "news", "price", "stock", "weather", "traffic", "events",
            "schedule", "hours", "open", "closed", "available"
        ]
        
        # Check for direct web search requests
        for indicator in web_search_indicators:
            if indicator in message_lower:
                return True
        
        # Check for current information topics
        for topic in current_info_topics:
            if topic in message_lower:
                return True
        
        return False


# Create handler instance
telephony_voice_agent_handler = TelephonyVoiceAgentHandler()


# WebSocket endpoint
async def telephony_voice_agent_websocket(websocket: WebSocket):
    """WebSocket endpoint for Twilio Voice Agent integration"""
    # Create database session manually (dependency injection doesn't work well with add_websocket_route)
    async for db in get_db():
        try:
            await telephony_voice_agent_handler.handle_connection(websocket, db)
        finally:
            # Ensure proper session cleanup
            try:
                await db.close()
            except Exception as cleanup_error:
                logger.error(f"❌ Error during database session cleanup: {cleanup_error}")
        break