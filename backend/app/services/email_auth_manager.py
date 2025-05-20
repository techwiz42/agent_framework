import logging
import json
import secrets
import time
from typing import Dict, Any, Optional, List, Union
import aiohttp
import base64
from urllib.parse import urlencode
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth configuration - these would come from environment variables in production
# OAuth configuration - these would come from environment variables in production
OAUTH_CONFIG = {
    "gmail": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uri": f"{settings.FRONTEND_URL}/email/callback",  # Use your frontend URL
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly", 
                  "https://www.googleapis.com/auth/gmail.send",
                  "https://www.googleapis.com/auth/gmail.modify",
                  "openid",
                  "email",
                  "profile"]
    },
    "outlook": {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
        "auth_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "redirect_uri": f"{settings.FRONTEND_URL}/email/callback",  # Use your frontend URL
        "scopes": ["openid", "offline_access", "Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"]
    }
}

# Storage for active OAuth sessions and tokens (would use a database in production)
# Maps user_id -> Dict of provider-specific tokens and data
active_sessions = {}

class EmailAuthManager:
    """Manages OAuth2 authentication for email providers"""
    
    @staticmethod
    def generate_auth_url(provider: str, user_id: str) -> str:
        """
        Generate the OAuth2 authorization URL for a specific provider.
        
        Args:
            provider: The email provider (gmail, outlook, etc.)
            user_id: The ID of the user requesting authentication
            
        Returns:
            The authorization URL for the user to visit
        """
        if provider.lower() not in OAUTH_CONFIG:
            raise ValueError(f"Unsupported provider: {provider}")
            
        config = OAUTH_CONFIG[provider.lower()]
        
        # Generate state token for CSRF protection
        state_token = secrets.token_urlsafe(32)
        
        # Store state in active sessions
        if user_id not in active_sessions:
            active_sessions[user_id] = {}
            
        active_sessions[user_id][provider] = {
            "state": state_token,
            "created_at": datetime.now(),
            "provider": provider
        }
        
        # Build authorization parameters
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state_token,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        # Construct the auth URL
        auth_url = f"{config['auth_uri']}?{urlencode(params)}"
        
        logger.info(f"Generated auth URL for {provider} - user: {user_id}")
        
        return auth_url
        
    @staticmethod
    async def exchange_code_for_token(provider: str, user_id: str, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token.
        
        Args:
            provider: The email provider (gmail, outlook, etc.)
            user_id: The ID of the user requesting authentication
            code: The authorization code received from the provider
            state: The state parameter for CSRF verification
            
        Returns:
            Token response data
        """
        # Verify state matches what we stored
        if (user_id not in active_sessions or 
            provider not in active_sessions[user_id] or
            active_sessions[user_id][provider]["state"] != state):
            raise ValueError("Invalid state token - possible CSRF attack")
            
        # Get provider config
        if provider.lower() not in OAUTH_CONFIG:
            raise ValueError(f"Unsupported provider: {provider}")
            
        config = OAUTH_CONFIG[provider.lower()]
        
        # Prepare token request
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": config["redirect_uri"],
            "grant_type": "authorization_code"
        }
        
        # Exchange code for token
        async with aiohttp.ClientSession() as session:
            async with session.post(config["token_uri"], data=token_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    raise ValueError(f"Failed to exchange code for token: {response.status}")
                    
                token_response = await response.json()
                
        # Store tokens in session
        active_sessions[user_id][provider].update({
            "access_token": token_response["access_token"],
            "refresh_token": token_response.get("refresh_token"),
            "token_type": token_response["token_type"],
            "expires_in": token_response["expires_in"],
            "expires_at": datetime.now() + timedelta(seconds=token_response["expires_in"]),
            "authenticated": True
        })
        
        # Get user info if available
        user_email = await EmailAuthManager.get_user_email(provider, user_id)
        if user_email:
            active_sessions[user_id][provider]["user_email"] = user_email
            
        return active_sessions[user_id][provider]
        
    @staticmethod
    async def refresh_token_if_needed(provider: str, user_id: str) -> Dict[str, Any]:
        """
        Refresh the access token if it's expired or about to expire.
        
        Args:
            provider: The email provider
            user_id: The user ID
            
        Returns:
            Updated token data
        """
        # Check if session exists
        if (user_id not in active_sessions or 
            provider not in active_sessions[user_id] or
            "refresh_token" not in active_sessions[user_id][provider]):
            raise ValueError("No valid session found")
            
        session_data = active_sessions[user_id][provider]
        
        # Check if token is expired or about to expire
        if (not session_data.get("expires_at") or
            datetime.now() >= session_data["expires_at"] - timedelta(minutes=5)):
            
            # Get provider config
            if provider.lower() not in OAUTH_CONFIG:
                raise ValueError(f"Unsupported provider: {provider}")
                
            config = OAUTH_CONFIG[provider.lower()]
            
            # Prepare refresh token request
            refresh_data = {
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "refresh_token": session_data["refresh_token"],
                "grant_type": "refresh_token"
            }
            
            # Get new access token
            async with aiohttp.ClientSession() as session:
                async with session.post(config["token_uri"], data=refresh_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: {error_text}")
                        
                        # Mark session as no longer authenticated
                        session_data["authenticated"] = False
                        return session_data
                        
                    token_response = await response.json()
                    
            # Update token data
            session_data.update({
                "access_token": token_response["access_token"],
                # Some providers don't return a new refresh token
                "refresh_token": token_response.get("refresh_token", session_data["refresh_token"]),
                "token_type": token_response["token_type"],
                "expires_in": token_response["expires_in"],
                "expires_at": datetime.now() + timedelta(seconds=token_response["expires_in"]),
                "authenticated": True
            })
            
            logger.info(f"Refreshed token for {provider} - user: {user_id}")
            
        return session_data
        
    @staticmethod
    async def get_user_email(provider: str, user_id: str) -> Optional[str]:
        """
        Get the user's email address from the provider.
        
        Args:
            provider: The email provider
            user_id: The user ID
            
        Returns:
            The user's email address if available
        """
        # Check if session exists
        if (user_id not in active_sessions or 
            provider not in active_sessions[user_id] or
            not active_sessions[user_id][provider].get("authenticated")):
            return None
            
        # Get token data
        session_data = active_sessions[user_id][provider]
        
        # Try to get user email based on provider
        if provider.lower() == "gmail":
            # Call Gmail API to get user profile
            profile_url = "https://www.googleapis.com/gmail/v1/users/me/profile"
            headers = {
                "Authorization": f"Bearer {session_data['access_token']}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(profile_url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get Gmail profile: {response.status}")
                        return None
                        
                    profile_data = await response.json()
                    return profile_data.get("emailAddress")
                    
        elif provider.lower() == "outlook":
            # Call Microsoft Graph API to get user profile
            profile_url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                "Authorization": f"Bearer {session_data['access_token']}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(profile_url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get Outlook profile: {response.status}")
                        return None
                        
                    profile_data = await response.json()
                    return profile_data.get("mail") or profile_data.get("userPrincipalName")
                    
        return None
        
    @staticmethod
    def is_authenticated(provider: str, user_id: str) -> bool:
        """
        Check if the user is authenticated with the provider.
        
        Args:
            provider: The email provider
            user_id: The user ID
            
        Returns:
            True if authenticated, False otherwise
        """
        return (user_id in active_sessions and 
                provider in active_sessions[user_id] and 
                active_sessions[user_id][provider].get("authenticated", False))
                
    @staticmethod
    def get_session_data(provider: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the session data for a provider.
        
        Args:
            provider: The email provider
            user_id: The user ID
            
        Returns:
            Session data if available
        """
        if not EmailAuthManager.is_authenticated(provider, user_id):
            return None
            
        return active_sessions[user_id][provider]
        
    @staticmethod
    def logout(provider: str, user_id: str) -> bool:
        """
        Log the user out of the provider.
        
        Args:
            provider: The email provider
            user_id: The user ID
            
        Returns:
            True if logout successful, False otherwise
        """
        if user_id in active_sessions and provider in active_sessions[user_id]:
            # In a real implementation, you might want to revoke the tokens
            # with the provider's API
            
            # Remove session data
            active_sessions[user_id].pop(provider, None)
            
            # If no more providers, remove user entry
            if not active_sessions[user_id]:
                active_sessions.pop(user_id, None)
                
            return True
            
        return False

# Create a singleton instance
email_auth_manager = EmailAuthManager()
