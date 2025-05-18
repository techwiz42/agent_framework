from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.security import create_password_reset_token, verify_password_reset_token
from app.db.session import db_manager
from app.core.security import (
                               auth_manager,
                               create_email_verification_token,
                               verify_email_token
                            )
from app.schemas.domain.schemas import Token, UserAuth, RegistrationResponse
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
    
    user = await auth_manager.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Authentication failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify email verification
    if not user.email_verified:
        logger.warning(f"Unverified email for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in"
        )
        
    access_token = auth_manager.create_access_token(
        data={
            "sub": user.username,
            "email": user.email,
            "user_id": str(user.id),
            "role": str(user.role)  # Convert role to string
        },
    )

    # Token data stored in the token itself and validated by auth_manager
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role
    )

@router.post("/register", response_model=RegistrationResponse)
async def register_user(
    request: Request,
    user_data: UserAuth,
    db: AsyncSession = Depends(db_manager.get_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
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
        
        # Create verification token
        verification_token = create_email_verification_token({"email": user_data.email})
        hashed_password = auth_manager.get_password_hash(user_data.password)
        
        user = await db_manager.create_user(
            db,
            user_data.username,
            user_data.email,
            hashed_password,
            verification_token=verification_token
        )
        
        # Create notification service and add to background tasks
        # In a full implementation, you would have a notification service to send emails
        # background_tasks.add_task(
        #     notification_service.send_verification_email,
        #     user_data.email,
        #     verification_token
        # )
        
        return {
            "message": "Registration pending. Please check your email to verify your account.",
            "email": user_data.email
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(db_manager.get_session)
):
    payload = verify_email_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    
    user = await db_manager.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.email_verified:
        return {"message": "Email already verified"}
    
    user.email_verified = True
    user.email_verification_token = None
    await db.commit()
    
    return {"message": "Email verified successfully"}

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
            # In a full implementation, you would have a notification service
            # background_tasks.add_task(
            #     notification_service.send_password_reset_email,
            #     email,
            #     reset_token
            # )
            logger.info(f"Password reset email would be sent to {email}")
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
    
    return {"message": "Password successfully reset"}

@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(auth_manager.get_current_user)
):
    """Logout the current user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Since we're not using session storage, we can't invalidate the token server-side.
    # Client will need to discard the token.
    
    return {"message": "Successfully logged out"}