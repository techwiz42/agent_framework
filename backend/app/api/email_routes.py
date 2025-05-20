from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any, Optional, List
import secrets
import json
import base64
import logging
from urllib.parse import urlencode
import requests
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.core.config import settings
from app.services.email_auth_manager import email_auth_manager

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/email", tags=["email"])

# Request models
class EmailAuthRequest(BaseModel):
    provider: str
    user_id: str

class EmailTokenRequest(BaseModel):
    provider: str
    user_id: str
    code: str
    state: str
    redirect_uri: str

class EmailStatusRequest(BaseModel):
    provider: str
    user_id: str

class EmailMessageRequest(BaseModel):
    provider: str
    user_id: str
    folder: str = "inbox"
    max_results: int = 10
    query: Optional[str] = None

class EmailReadRequest(BaseModel):
    provider: str
    user_id: str
    message_id: str

class EmailSendRequest(BaseModel):
    provider: str
    user_id: str
    to: str
    subject: str
    body: str
    body_type: str = "html"
    cc: Optional[str] = None
    bcc: Optional[str] = None

class EmailLogoutRequest(BaseModel):
    provider: str
    user_id: str

# Response models
class EmailAuthResponse(BaseModel):
    auth_url: str
    state: str

class EmailTokenResponse(BaseModel):
    status: str
    provider: str
    email: Optional[str] = None
    access_token: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None

class EmailStatusResponse(BaseModel):
    status: str
    authenticated: bool
    provider: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[str] = None

def generate_auth_state(provider: str, user_id: str) -> str:
    """Generate a secure state parameter for CSRF protection"""
    state_data = {
        "provider": provider,
        "user_id": str(user_id),
        "timestamp": datetime.now().timestamp()
    }
    
    # Add random component for CSRF protection
    state_data["csrf_token"] = secrets.token_urlsafe(16)
    
    # Encode as URL-safe base64
    return base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

def decode_auth_state(state: str) -> Dict[str, Any]:
    """Decode state parameter to get user and provider info"""
    try:
        state_data = json.loads(base64.urlsafe_b64decode(state + "=" * (-len(state) % 4)).decode())
        return state_data
    except Exception as e:
        logger.error(f"Failed to decode state parameter: {e}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

@router.post("/authorize", response_model=EmailAuthResponse)
async def email_authorize(request: EmailAuthRequest):
    """Generate an authorization URL for email provider OAuth"""
    try:
        # Generate state parameter
        state = generate_auth_state(request.provider, request.user_id)
        
        # Generate auth URL based on provider
        if request.provider.lower() == "gmail":
            # Google OAuth URL
            scopes = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.modify",
                "openid",
                "email",
                "profile"
            ]
            
            params = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": f"{settings.FRONTEND_URL}/email/callback",
                "response_type": "code",
                "scope": " ".join(scopes),
                "state": state,
                "access_type": "offline",
                "prompt": "consent"
            }
            
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
            
        elif request.provider.lower() == "outlook":
            # Microsoft OAuth URL
            scopes = [
                "openid",
                "offline_access",
                "Mail.Read",
                "Mail.ReadWrite",
                "Mail.Send",
                "User.Read"
            ]
            
            params = {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "redirect_uri": f"{settings.FRONTEND_URL}/email/callback",
                "response_type": "code",
                "scope": " ".join(scopes),
                "state": state,
                "prompt": "consent"
            }
            
            auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported email provider: {request.provider}")
            
        return EmailAuthResponse(auth_url=auth_url, state=state)
        
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")

@router.post("/token", response_model=EmailTokenResponse)
async def email_token(request: EmailTokenRequest):
    """Exchange authorization code for access token"""
    try:
        # Decode state to verify integrity
        state_data = decode_auth_state(request.state)
        
        # Verify that the provider and user_id match
        if state_data["provider"] != request.provider:
            raise HTTPException(status_code=400, detail="Provider mismatch in state parameter")
            
        if state_data["user_id"] != str(request.user_id):
            raise HTTPException(status_code=400, detail="User ID mismatch in state parameter")
            
        # Exchange code for token based on provider
        if request.provider.lower() == "gmail":
            # Google token exchange
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": request.code,
                "redirect_uri": request.redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(token_url, data=data)
            
            if not response.ok:
                logger.error(f"Google token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
                
            token_data = response.json()
            
            # Store token in auth manager
            await email_auth_manager.exchange_code_for_token(
                request.provider, request.user_id, request.code, state_data["csrf_token"]
            )
            
            # Get user email
            user_email = await email_auth_manager.get_user_email(request.provider, request.user_id)
            
            return EmailTokenResponse(
                status="success",
                provider=request.provider,
                email=user_email,
                access_token=token_data.get("access_token"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token")
            )
            
        elif request.provider.lower() == "outlook":
            # Microsoft token exchange
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "code": request.code,
                "redirect_uri": request.redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(token_url, data=data)
            
            if not response.ok:
                logger.error(f"Microsoft token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
                
            token_data = response.json()
            
            # Store token in auth manager
            await email_auth_manager.exchange_code_for_token(
                request.provider, request.user_id, request.code, state_data["csrf_token"]
            )
            
            # Get user email
            user_email = await email_auth_manager.get_user_email(request.provider, request.user_id)
            
            return EmailTokenResponse(
                status="success",
                provider=request.provider,
                email=user_email,
                access_token=token_data.get("access_token"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token")
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported email provider: {request.provider}")
            
    except Exception as e:
        logger.error(f"Error exchanging code for token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to exchange code for token: {str(e)}")

@router.post("/status", response_model=EmailStatusResponse)
async def email_status(request: EmailStatusRequest):
    """Check authentication status for email provider"""
    try:
        # Check if authenticated
        is_authenticated = email_auth_manager.is_authenticated(request.provider, request.user_id)
        
        # If authenticated, get session data
        if is_authenticated:
            session_data = email_auth_manager.get_session_data(request.provider, request.user_id)
            
            return EmailStatusResponse(
                status="success",
                authenticated=True,
                provider=request.provider,
                email=session_data.get("user_email"),
                expires_at=session_data.get("expires_at", "").isoformat() if session_data.get("expires_at") else None
            )
        else:
            return EmailStatusResponse(
                status="success",
                authenticated=False,
                provider=request.provider
            )
            
    except Exception as e:
        logger.error(f"Error checking email status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check authentication status: {str(e)}")

@router.post("/logout")
async def email_logout(request: EmailLogoutRequest):
    """Log out from email provider"""
    try:
        # Log out from provider
        success = email_auth_manager.logout(request.provider, request.user_id)
        
        return {"status": "success" if success else "error", "message": "Logged out successfully" if success else "Not logged in"}
        
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log out: {str(e)}")

@router.post("/messages")
async def list_messages(request: EmailMessageRequest):
    """List messages from email provider"""
    try:
        # Import here to avoid circular imports
        from app.services.agents.agent_email_service import agent_email_service
        
        # Check if authenticated
        if not email_auth_manager.is_authenticated(request.provider, request.user_id):
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # List messages
        messages = await agent_email_service.list_messages(
            provider=request.provider,
            user_id=request.user_id,
            folder=request.folder,
            max_results=request.max_results,
            query=request.query
        )
        
        return {"status": "success", "messages": messages}
        
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")

@router.post("/messages/read")
async def read_message(request: EmailReadRequest):
    """Read a specific message"""
    try:
        # Import here to avoid circular imports
        from app.services.agents.agent_email_service import agent_email_service
        
        # Check if authenticated
        if not email_auth_manager.is_authenticated(request.provider, request.user_id):
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Get message
        message = await agent_email_service.get_message(
            provider=request.provider,
            user_id=request.user_id,
            message_id=request.message_id
        )
        
        return {"status": "success", "message": message}
        
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read message: {str(e)}")

@router.post("/messages/send")
async def send_message(request: EmailSendRequest):
    """Send an email message"""
    try:
        # Import here to avoid circular imports
        from app.services.agents.agent_email_service import agent_email_service
        
        # Check if authenticated
        if not email_auth_manager.is_authenticated(request.provider, request.user_id):
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Send message
        result = await agent_email_service.send_message(
            provider=request.provider,
            user_id=request.user_id,
            to=request.to,
            subject=request.subject,
            body=request.body,
            body_type=request.body_type,
            cc=request.cc,
            bcc=request.bcc
        )
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.post("/messages/search")
async def search_messages(request: EmailMessageRequest):
    """Search for messages matching a query"""
    try:
        # Import here to avoid circular imports
        from app.services.agents.agent_email_service import agent_email_service
        
        # Check if authenticated
        if not email_auth_manager.is_authenticated(request.provider, request.user_id):
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Use the query parameter for search
        if not request.query:
            raise HTTPException(status_code=400, detail="Query parameter is required for search")
            
        # Search messages
        messages = await agent_email_service.search_messages(
            provider=request.provider,
            user_id=request.user_id,
            query=request.query,
            max_results=request.max_results,
            folder=request.folder
        )
        
        return {"status": "success", "messages": messages}
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {str(e)}")
