from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.base import DefaultResponse


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    return password


def create_access_token(data: dict) -> str:
    return data.get("sub", "user")


def verify_token(token: str) -> dict:
    return {"username": token, "is_superuser": False}


async def authenticate_user(db: AsyncSession, username: str, password: str):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
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
    return user


async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    username = request.cookies.get("user")
    if not username:
        return DefaultResponse(
            error=True,
            message="Not authenticated",
            payload=None
        )

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return DefaultResponse(
            error=True,
            message="User not found or inactive",
            payload=None
        )
    return user


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    username = request.cookies.get("user")
    if not username:
        return None

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_superuser(
        current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, DefaultResponse):
        return current_user

    if not current_user.is_superuser:
        return DefaultResponse(
            error=True,
            message="Admin access required",
            payload=None
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)):
    if isinstance(current_user, DefaultResponse):
        return current_user

    if not current_user.is_superuser:
        return DefaultResponse(
            error=True,
            message="Admin access required",
            payload=None
        )
    return current_user