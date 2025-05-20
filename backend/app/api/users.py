from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import db_manager
from app.models.domain.models import User
from pydantic import BaseModel
from app.core.security import auth_manager
import logging

logger = logging.getLogger(__name__)

class AddTokensRequest(BaseModel):
    tokens: int

class TokensResponse(BaseModel):
    tokens_purchased: int
    tokens_consumed: int
    tokens_remaining: int

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{user_id}/tokens", response_model=TokensResponse)
async def get_user_tokens(
    user_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    # Verify user is requesting their own tokens or is an admin
    if str(current_user.id) != str(user_id) and str(current_user.role) != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to view this user's tokens")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "tokens_purchased": user.tokens_purchased,
        "tokens_consumed": user.tokens_consumed,
        "tokens_remaining": user.tokens_remaining
    }

@router.post("/{user_id}/add-tokens")
async def add_user_tokens(
    user_id: UUID,
    token_data: AddTokensRequest,  
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    # Verify user is modifying their own tokens or is an admin
    if str(current_user.id) != str(user_id) and str(current_user.role) != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to modify this user's tokens")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.tokens_purchased += token_data.tokens
    await db.commit()

    # No need to invalidate cache as we're not using Redis anymore

    return {"message": f"{token_data.tokens} tokens added to user {user_id}"}

@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    # Verify user is requesting their own profile or is an admin
    if str(current_user.id) != str(user_id) and str(current_user.role) != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to view this user's profile")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user profile without sensitive data
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,  # Convert datetime to string
        "role": str(user.role),  # Convert Enum to string
        "preferences": user.preferences,
        "is_active": user.is_active,
        "email_verified": user.email_verified
    }

@router.post("/{user_id}/update-token-usage")
async def update_token_usage(
    user_id: UUID,
    token_data: dict,
    db: AsyncSession = Depends(db_manager.get_session),
    current_user = Depends(auth_manager.get_current_user)
):
    """Update token usage for a user (for internal system use)"""
    # Only allow admins or the system user to update token usage
    if str(current_user.role) != 'admin' and str(current_user.role) != 'system':
        raise HTTPException(status_code=403, detail="Not authorized to update token usage")
    
    tokens_used = token_data.get("tokens_used", 0)
    if tokens_used <= 0:
        raise HTTPException(status_code=400, detail="Invalid token count")
    
    try:
        # Use an UPDATE statement rather than loading the full user object
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(tokens_consumed=User.tokens_consumed + tokens_used)
            .returning(User.tokens_consumed, User.tokens_purchased)
        )
        
        result = await db.execute(stmt)
        updated_values = result.fetchone()
        await db.commit()
        
        if not updated_values:
            raise HTTPException(status_code=404, detail="User not found")
        
        # No need to invalidate cache as we're not using Redis anymore
        
        tokens_consumed, tokens_purchased = updated_values
        
        return {
            "tokens_consumed": tokens_consumed,
            "tokens_purchased": tokens_purchased,
            "tokens_remaining": tokens_purchased - tokens_consumed
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating token usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to update token usage")
