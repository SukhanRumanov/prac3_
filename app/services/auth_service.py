# services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.base import DefaultResponse
from app.schemas.auth import Token
import logging

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, username: str, password: str):

    try:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Пользователь не найден: {username}")
            return DefaultResponse(
                error=True,
                message="Invalid credentials",
                payload=None
            )

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Неверный пароль для пользователя: {username}")
            return DefaultResponse(
                error=True,
                message="Invalid credentials",
                payload=None
            )

        if not user.is_active:
            logger.warning(f"Попытка входа неактивного пользователя: {username}")
            return DefaultResponse(
                error=True,
                message="Inactive user",
                payload=None
            )

        return user

    except Exception as e:
        logger.error(f"Ошибка при аутентификации пользователя {username}: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Authentication error: {str(e)}",
            payload=None
        )


def create_user_access_token(user: User) -> str:
    return create_access_token(data={"sub": user.username})


async def login_user(
        db: AsyncSession,
        username: str,
        password: str
) :
    auth_result = await authenticate_user(db, username, password)

    if isinstance(auth_result, DefaultResponse):
        return auth_result

    user = auth_result
    access_token = create_user_access_token(user)

    logger.info(f"Успешный вход пользователя: {username} (ID: {user.id})")
    return Token(access_token=access_token, token_type="bearer")