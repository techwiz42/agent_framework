from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.security import create_password_reset_token, verify_password_reset_token
from app.db.session import db_manager
from app.core.security import auth_manager
from app.schemas.domain.schemas import Token, UserAuth, RegistrationResponse
from app.services.notifications import NotificationService
from pydantic import BaseModel, Field
import traceback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_manager.get_session)
):
    logger.info(f"Login attempt for username: {form_data.username}")
    
    # Try to authenticate by email instead of username
    user = await auth_manager.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Authentication failed for username/email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    access_token = auth_manager.create_access_token(
        data={
            "sub": user.username,
            "email": user.email,
            "user_id": str(user.id),
            "role": str(user.role),  # Convert role to string
            "phone": user.phone
        },
    )

    # Token data stored in the token itself and validated by auth_manager
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role
    )

@router.post("/register", response_model=RegistrationResponse)
async def register_user(
    request: Request,
    user_data: UserAuth,
    db: AsyncSession = Depends(db_manager.get_session)
):
    try:
        # Check if passwords match
        if user_data.password != user_data.password_confirm:
            raise HTTPException(status_code=400, detail="Passwords do not match")
            
        # Check for existing username
        existing_user = await db_manager.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check for existing email
        existing_email = await db_manager.get_user_by_email(db, user_data.email)
        if existing_email:
            return {
                "message": "This email address is already registered. Please log in or use the password reset feature if you forgot your password.",
                "email": user_data.email
            }
        
        hashed_password = auth_manager.get_password_hash(user_data.password)
        
        user = await db_manager.create_user(
            db,
            user_data.username,
            user_data.email,
            hashed_password,
            phone=user_data.phone
        )
        
        return {
            "message": "Registration successful. You can now log in.",
            "email": user_data.email
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

# Email verification endpoint removed since we no longer need email verification
# The endpoint at /api/auth/verify-email/{token} has been removed

@router.post("/request-password-reset")
async def request_password_reset(
    request: Request,
    request_data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Request password reset link."""
    email = request_data.get('email')
    logger.info(f"Password reset requested for email: {email}")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        user = await db_manager.get_user_by_email(db, email)
        if user:
            reset_token = create_password_reset_token(email)
            notification_service = NotificationService()
            
            # Add to background tasks
            background_tasks.add_task(
                notification_service.send_password_reset_email,
                email,
                reset_token
            )
            logger.info(f"Password reset email queued for {email}")
        else:
            logger.info(f"Password reset requested for non-existent email: {email}")
            
        # Always return the same message whether user exists or not
        return {
            "message": "If a matching account was found, password reset instructions have been sent to your email"
        }
        
    except Exception as e:
        logger.error(f"Error processing password reset request: {e}")
        # Don't expose internal errors to the user
        return {
            "message": "If a matching account was found, password reset instructions have been sent to your email"
        }

class PasswordResetRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

@router.post("/reset-password")
async def reset_password(
    request: Request,
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Reset password using token."""
    email = verify_password_reset_token(reset_request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = await db_manager.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    hashed_password = auth_manager.get_password_hash(reset_request.new_password)
    
    # Update user's password
    user.hashed_password = hashed_password
    await db.commit()
    
    # No need to invalidate tokens as we're not using Redis caching anymore
    
    return {"message": "Password successfully reset"}

@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(auth_manager.get_current_user)
):
    """Logout the current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Since we're not using Redis for token storage/blacklisting,
    # we can't invalidate the token server-side. Client will need to
    # discard the token.
    
    return {"message": "Successfully logged out"}
