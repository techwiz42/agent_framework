from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, List
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from uuid import UUID
import logging
import os

from app.db.session import db_manager
from app.models.domain.models import User, ThreadParticipant

# Configure logging
logger = logging.getLogger(__name__)

# Constants and configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # One hour

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

class RateLimitExceeded(HTTPException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

class SecurityManager:
    def __init__(self):
        self.pwd_context = pwd_context
        self.api_key_cache: Dict[str, List[datetime]] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.blocked_ips: Dict[str, datetime] = {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
        
    def create_access_token(self, data: Dict) -> str:
        user = data.get('user')  # Get full user object if available
        if user and user.role and hasattr(user.role, "value"):
            role = user.role.value
        elif user and user.role:
            role = str(user.role)
        else:
            role = "USER"
        to_encode = {
            "sub": data["sub"],
            "email": user.email if user else data.get("email"),
            "user_id": str(user.id) if user else data.get("user_id"),
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_invitation_token(self, data: Dict) -> str:
        """
        Create a token for thread invitation.
        
        Args:
            data: Dictionary containing thread_id and participant email
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 day expiry for invitations
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_invitation_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode an invitation token.

        Args:
            token: The invitation token to verify

        Returns:
            Dict with thread_id and email if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            thread_id = payload.get("thread_id")
            email = payload.get("email")

            if not thread_id or not email:
                logger.warning("Invalid token payload structure")
                return None

            return {"thread_id": thread_id, "email": email}
    
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None

        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return None

    def create_token_url(self, thread_id: str, email: str, base_url: str) -> str:
        """
        Create a full invitation URL with token.
        
        Args:
            thread_id: The UUID of the thread
            email: The participant's email
            base_url: The base URL of the frontend
            
        Returns:
            Complete invitation URL
        """
        token = self.create_invitation_token({
            "thread_id": str(thread_id),
            "email": email
        })
        return f"{base_url}/join/{token}"

    async def verify_participant_access(
        self,
        db: AsyncSession,
        thread_id: UUID,
        email: str
    ) -> bool:
        """
        Verify if an email address has participant access to a thread.
        
        Args:
            db: Database session
            thread_id: Thread UUID
            email: Participant email to verify
            
        Returns:
            True if participant has access, False otherwise
        """
        try:
            result = await db.execute(
                select(ThreadParticipant)
                .where(ThreadParticipant.thread_id == thread_id)
                .where(ThreadParticipant.email == email)
                .where(ThreadParticipant.is_active == True)
            )
            participant = result.scalar_one_or_none()
            return participant is not None
            
        except Exception as e:
            logger.error(f"Error verifying participant access: {e}")
            return False


    async def authenticate_user(self, db: AsyncSession, identifier: str, password: str):
        try:
            # Check if identifier is an email or username
            result = await db.execute(
                select(User).where(
                    or_(
                        User.username == identifier,
                        User.email == identifier
                    )
                )
            )
            user = result.scalar_one_or_none()
        
            if not user or not self.verify_password(password, user.hashed_password):
                return None
            
            user.last_login = datetime.utcnow()
            await db.commit()
            return user
        except:
            await db.rollback()
            raise

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(db_manager.get_session)
    ):
        """Validate HTTP request token with exceptions"""
        credentials_exception = HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
            # Check if this is a participant token
            if payload.get('type') == 'participant':
                email = payload.get('email')
                thread_id = UUID(payload.get('thread_id'))
            
                # Find the participant
                result = await db.execute(
                    select(ThreadParticipant)
                    .where(
                        and_(
                            ThreadParticipant.thread_id == thread_id,
                            ThreadParticipant.email == email
                        )
                    )
                )
                participant = result.scalar_one_or_none()
            
                if not participant:
                    raise credentials_exception
            
                return type('ParticipantUser', (), {
                    'id': participant.id,
                    'username': email,  # Use email as username
                    'email': email,
                    'name': participant.name
                })
        
            # Regular user authentication
            # Try to find by username or email
            username = payload.get("sub")
            if not username:
                raise credentials_exception
        
            # Try to find user by username or email
            result = await db.execute(
                select(User)
                .where(or_(
                    User.username == username,
                    User.email == username
                ))
            )
            user = result.scalar_one_or_none()
        
            if not user:
                raise credentials_exception
        
            return user
    
        except JWTError:
            raise credentials_exception
    async def get_current_user_ws(self, token: str, db: AsyncSession) -> Optional[User]:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
            # Handle participant tokens
            if payload.get('type') == 'participant':
                email = payload.get('email')
                thread_id = UUID(payload.get('thread_id'))
            
                result = await db.execute(
                    select(ThreadParticipant)
                    .where(
                        ThreadParticipant.thread_id == thread_id,
                        ThreadParticipant.email == email
                    )
                )
                participant = result.scalar_one_or_none()
            
                if not participant:
                    return None
            
                # Approach 1: Convert ID to string
                participant_user = type('ParticipantUser', (), {
                    'id': str(participant.id),  # Convert UUID to string
                    'username': email,
                    'email': email,
                    'name': participant.name
                })
            
                # Approach 2: Add method to check participation
                setattr(participant_user, 'is_thread_participant', 
                        lambda thread_id, db: db_manager.is_thread_participant(db, thread_id, email))
            
                return participant_user

            # Regular user authentication logic
            username = payload.get("sub")
            if not username:
                return None
        
            result = await db.execute(
                select(User)
                .where(or_(
                    User.username == username,
                    User.email == username
                ))
            )
            user = result.scalar_one_or_none()
            return user

        except Exception as e:
            logger.error(f"WebSocket user authentication error: {e}")
            return None

    async def cleanup(self):
        """Remove expired entries from caches."""
        current_time = datetime.now(UTC)
        
        # Clean api_key_cache - remove old timestamps
        for key in list(self.api_key_cache.keys()):
            self.api_key_cache[key] = [
                ts for ts in self.api_key_cache[key]
                if (current_time - ts).total_seconds() < 3600
            ]
            if not self.api_key_cache[key]:
                del self.api_key_cache[key]
        
        # Clean blocked_ips
        self.blocked_ips = {
            k: v for k, v in self.blocked_ips.items()
            if v > current_time
        }

    async def check_rate_limit(self, request: Request, limit: str, duration: int):
        """
        Check rate limit for request.
        
        Args:
            request: FastAPI Request object
            limit: String in format "X/timeunit" (e.g. "5/second")
            duration: Time window in seconds
        """
        client_ip = request.client.host
        cache_key = f"{client_ip}:{request.url.path}"
        current_time = datetime.now(UTC)
        max_requests = int(limit.split('/')[0])

        # Initialize timestamps list if not exists
        if cache_key not in self.api_key_cache:
            self.api_key_cache[cache_key] = []
        
        # Clean old timestamps
        self.api_key_cache[cache_key] = [
            ts for ts in self.api_key_cache[cache_key]
            if (current_time - ts).total_seconds() < duration
        ]
        
        # Check if limit exceeded
        if len(self.api_key_cache[cache_key]) >= max_requests:
            raise RateLimitExceeded()
        
        # Record this request
        self.api_key_cache[cache_key].append(current_time)

    async def check_blocked_ip(self, request: Request):
        """Check if IP is blocked."""
        client_ip = request.client.host
        current_time = datetime.now(UTC)
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                raise HTTPException(
                    status_code=403,
                    detail="IP address is blocked"
                )
            else:
                del self.blocked_ips[client_ip]

    async def record_failed_attempt(self, request: Request):
        """Record failed authentication attempt."""
        client_ip = request.client.host
        self.failed_attempts[client_ip] = self.failed_attempts.get(client_ip, 0) + 1
        
        if self.failed_attempts[client_ip] >= 5:
            self.blocked_ips[client_ip] = datetime.now(UTC) + timedelta(minutes=15)
            del self.failed_attempts[client_ip]

    def create_participant_token(self, thread_id: UUID, email: str, name: str = None) -> str:
        """Create a token specifically for conversation participants."""
        to_encode = {
            'sub': email,  # use email as subject
            'thread_id': str(thread_id),
            'email': email,
            'name': name,
            'type': 'participant',  # distinguish from regular user tokens
            'exp': datetime.utcnow() + timedelta(days=30)  # longer expiry for participants
        }
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    async def get_participant_from_token(self, token: str, db: AsyncSession) -> Optional[ThreadParticipant]:
        """Validate participant token and return participant info."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            if payload.get('type') != 'participant':
                return None

            thread_id = UUID(payload.get('thread_id'))
            email = payload.get('email')

            if not thread_id or not email:
                return None

            result = await db.execute(
                select(ThreadParticipant)
                .where(
                    and_(
                        ThreadParticipant.thread_id == thread_id,
                        ThreadParticipant.email == email
                    )
                )
            )
            return result.scalar_one_or_none()

        except JWTError:
            return None

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=403,
                detail="Invalid authentication credentials"
            )

        scheme, _, token = auth_header.partition(" ")
        if not scheme or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=403,
                detail="Invalid authentication scheme"
            )

        if not token:
            raise HTTPException(
                status_code=403,
                detail="Invalid authentication credentials"
            )
            
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=403,
                detail="Invalid token"
            )
            
        return payload

# Rate limit decorators
def rate_limit(limit: str, duration: int):
    """Rate limit decorator."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            await security_manager.check_rate_limit(request, limit, duration)
            return await func(request=request, *args, **kwargs)
        return wrapper
    return decorator

# Email verification token functions removed as they are no longer needed

def create_password_reset_token(email: str) -> str:
    """Generate a time-limited password reset token."""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify and return email from password reset token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get('email')
    except JWTError:
        return None

# Create security manager instance
security_manager = SecurityManager()

# For backward compatibility with existing code
auth_manager = security_manager
