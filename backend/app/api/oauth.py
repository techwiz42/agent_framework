from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Dict
import requests
from urllib.parse import urlencode
from pydantic import BaseModel
import secrets
import hashlib
import base64
import json
import traceback
import logging
from app.core.config import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/oauth", tags=["oauth"])

class TokenRequest(BaseModel):
    code: str
    redirect_uri: str
    state: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class GoogleAccessToken(BaseModel):
    access_token: str

def generate_code_verifier() -> str:
    """Generate a random code verifier for PKCE"""
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier: str) -> str:
    """Create a code challenge from the code verifier using SHA256"""
    sha256_hash = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256_hash).decode().rstrip('=')

def create_state_token(verifier: str) -> str:
    """Create a state token that includes the verifier."""
    state_data = {
        'v': verifier,  # verifier
        'r': secrets.token_urlsafe(16)  # random component
    }
    return base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

def decode_state_token(state: str) -> dict:
    """Decode the state token to get the verifier."""
    try:
        state_data = json.loads(base64.urlsafe_b64decode(state + '=' * (-len(state) % 4)))
        return state_data
    except Exception as e:
        logger.error(f"Error decoding state token: {e}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

#############################################
#           Google OAuth Implementation
############################################

@router.get("/google/authorize")
async def google_authorize():
    """Initiate Google OAuth code flow with PKCE"""
    try:
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = create_state_token(code_verifier)
        
        logger.info(f"Starting Google OAuth flow with code verifier (first 5 chars): {code_verifier[:5]}...")
        logger.info(f"Generated state token (first 10 chars): {state[:10]}...")
        
        # Try a broader set of scopes - include full drive access
        scopes = [
            'https://www.googleapis.com/auth/drive',        # Full Drive access
            'https://www.googleapis.com/auth/drive.file',   # Per-file access
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly',
            'profile', 
            'email',
            'openid'
        ]
        
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': 'https://cyberiad.ai/google-callback',
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',       # Ensures we get a refresh token
            'prompt': 'consent',            # Force consent screen to ensure refresh token
            'include_granted_scopes': 'true' # Include previously granted scopes
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        logger.info(f"Redirecting to Google OAuth URL with scopes: {' '.join(scopes)}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error in Google authorization: {e}")
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")

@router.post("/google/token")
async def google_token(request: TokenRequest):
    """Exchange authorization code for tokens"""
    try:
        # Get verifier from state
        logger.info(f"Received token request with code (first 5 chars): {request.code[:5]}...")
        logger.info(f"State token (first 10 chars): {request.state[:10]}...")
        logger.info(f"Redirect URI: {request.redirect_uri}")
        
        state_data = decode_state_token(request.state)
        code_verifier = state_data['v']
        logger.info(f"Decoded code verifier (first 5 chars): {code_verifier[:5]}...")
        
        # Use the same broader set of scopes
        scopes = [
            'https://www.googleapis.com/auth/drive',        # Full Drive access
            'https://www.googleapis.com/auth/drive.file',   # Per-file access
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly',
            'profile', 
            'email',
            'openid'
        ]
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': request.code,
            'redirect_uri': request.redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
            'scope': ' '.join(scopes)
        }
        
        logger.info(f"Making token request to: {token_url}")
        response = requests.post(token_url, data=data)
        
        # Log full response details (be careful with sensitive info)
        logger.info(f"Token response status: {response.status_code}")
        if not response.ok:
            logger.error(f"Token exchange failed: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to exchange code for token: {response.text}"
            )
        
        # Process the token response
        token_data = response.json()
        logger.info(f"Token response keys: {token_data.keys()}")
        
        # Check for required fields
        required_fields = ['access_token', 'token_type', 'expires_in']
        for field in required_fields:
            if field not in token_data:
                logger.error(f"Missing required field in token response: {field}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field in token response: {field}"
                )
        
        # Check for refresh token specifically (important for long-term access)
        if 'refresh_token' not in token_data:
            logger.warning("No refresh token in response - user may have previously granted access")
        else:
            logger.info("Refresh token successfully received")
        
        # Validate scope in response
        if 'scope' in token_data:
            received_scopes = token_data['scope'].split(' ')
            logger.info(f"Received scopes: {received_scopes}")
            
            # Check if we got any drive scope
            drive_scopes = [s for s in received_scopes if 'drive' in s]
            if not drive_scopes:
                logger.warning("No Drive scopes found in token response!")
                logger.warning("This will cause 401 errors when accessing Google Drive API")
        
        logger.info("Token exchange successful")
        return token_data
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception(f"Unexpected error in token exchange: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to exchange code for token: {str(e)}"
            )
        raise

@router.post("/google/refresh")
async def refresh_google_token(request: RefreshTokenRequest):
    """Refresh Google Drive access token"""
    try:
        logger.info(f"Refreshing token with refresh_token (first 5 chars): {request.refresh_token[:5]}...")
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'refresh_token': request.refresh_token,
            'grant_type': 'refresh_token',
            'scope': ' '.join([
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.metadata.readonly'
            ])
        }
        
        logger.info(f"Making refresh request to: {token_url}")
        response = requests.post(token_url, data=data)
        
        if not response.ok:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to refresh token: {response.text}"
            )
        
        token_data = response.json()
        logger.info(f"Token refresh successful, new token keys: {token_data.keys()}")
        
        # Add back the refresh token if it's not in the response
        # Google doesn't include it in refresh responses, but clients might expect it
        if 'refresh_token' not in token_data:
            token_data['refresh_token'] = request.refresh_token
            logger.info("Added original refresh token to response")
        
        return token_data
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception(f"Unexpected error in token refresh: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh token: {str(e)}"
            )
        raise

#############################################
#           OneDrive Auth Code
############################################

ms_oauth_url = "https://login.microsoftonline.com/common/oauth2/v2.0"

@router.get("/onedrive/authorize")
async def onedrive_authorize():
    """Initiate OneDrive OAuth implicit flow"""
    # Generate a state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Define scopes - broad file access
    scope = ' '.join([
        'openid',  # Standard OpenID Connect scope
        'offline_access',  # Allows receiving refresh tokens
        'files.readwrite.all',  # Full file read/write access
        'user.read'  # Basic user profile access
    ])
    
    params = {
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'redirect_uri': 'https://cyberiad.ai/onedrive-callback',
        'response_type': 'token',  # Implicit flow
        'scope': scope,
        'state': state,
        'prompt': 'consent'  # Ensure user sees consent screen
    }   
    
    # Construct the authorization URL
    auth_url = f"{ms_oauth_url}/authorize?{urlencode(params)}"
    
    # Log for debugging (consider removing in production)
    
    return RedirectResponse(auth_url)

@router.post("/onedrive/token")
async def onedrive_token(request: TokenRequest):
    """Exchange authorization code for tokens"""
    try:
        # Get verifier from state
        state_data = decode_state_token(request.state)
        code_verifier = state_data['v']
        
        # Must match scopes from authorize endpoint
        scope = ' '.join([
            'offline_access',
            'files.read',
            'files.read.all'
        ])
        
        token_url = f"{ms_oauth_url}/token"
        data = {
            'client_id': settings.MICROSOFT_CLIENT_ID,
            'client_secret': settings.MICROSOFT_CLIENT_SECRET,
            'code': request.code,
            'redirect_uri': request.redirect_uri,
            'grant_type': 'authorization_code',
            'code_verifier': code_verifier,
            'scope': scope
        }
        
        
        response = requests.post(token_url, data=data)
        
        # Log the response details
        
        if not response.ok:
            error_text = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to exchange code for token: {error_text}"
            )
        
        token_data = response.json()
        
        # Check for refresh token
        if 'refresh_token' not in token_data:
            raise HTTPException(
                status_code=400,
                detail="No refresh token received. Please ensure you granted consent to the application."
            )
        
        return token_data
        
    except Exception as e:
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Token exchange error: {str(e)}"
        )

@router.post("/onedrive/refresh")
async def onedrive_refresh_token(request: RefreshTokenRequest):
    """Refresh OneDrive access token"""
    try:
        token_url = f"{ms_oauth_url}/token"
        refresh_data = {
            'client_id': settings.MICROSOFT_CLIENT_ID,
            'client_secret': settings.MICROSOFT_CLIENT_SECRET,
            'refresh_token': request.refresh_token,
            'grant_type': 'refresh_token',
            'scope': ' '.join([
                'offline_access',
                'files.read',
                'files.read.all'
            ])
        }
        
        response = requests.post(token_url, data=refresh_data)
        
        if not response.ok:
            logger.error(f"Token refresh failed: {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to refresh token: {response.text}"
            )
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a test endpoint to verify the router is working
@router.get("/test")
async def oauth_test():
    """Test endpoint to verify the OAuth router is working"""
    return {
        "status": "OAuth router is working",
        "google_client_id_prefix": settings.GOOGLE_CLIENT_ID[:5] + "...",
        "microsoft_client_id_prefix": settings.MICROSOFT_CLIENT_ID[:5] + "..." if hasattr(settings, "MICROSOFT_CLIENT_ID") else "Not set"
    }
