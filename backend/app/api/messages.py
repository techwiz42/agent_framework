from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import db_manager
from app.core.security import auth_manager
from app.schemas.domain.schemas import Token, UserAuth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=Token)
async def register_user(
    user_data: UserAuth,
    db: AsyncSession = Depends(db_manager.get_session)
):
    try:
        existing_user = await db_manager.get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )
        
        hashed_password = auth_manager.get_password_hash(user_data.password)
        user = await db_manager.create_user(db, user_data.username, user_data.email, hashed_password)
        
        access_token = auth_manager.create_access_token(data={"sub": user.username})
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_manager.get_session)
):
    user = await auth_manager.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = auth_manager.create_access_token(data={"sub": user.username})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username
    )
