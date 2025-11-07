from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserLogin, Token
from app.api.dependencies import get_current_user_optional
from app.core.security import verify_password, create_access_token
from app.schemas.base import DefaultResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        return DefaultResponse(
            error=True,
            message="Invalid credentials",
            payload=None
        )

    if not user.is_active:
        return DefaultResponse(
            error=True,
            message="Inactive user",
            payload=None
        )

    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=DefaultResponse)
async def read_users_me(current_user: dict = Depends(get_current_user_optional)):
    if not current_user:
        return DefaultResponse(
            error=True,
            message="User not authenticated",
            payload=None
        )

    return DefaultResponse(
        error=False,
        message="Success",
        payload=current_user
    )