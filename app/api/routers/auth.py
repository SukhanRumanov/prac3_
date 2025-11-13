from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserLogin, Token
from app.core.security import get_current_user_optional
from app.core.security import verify_password, create_access_token
from app.schemas.base import DefaultResponse
from app.logger.logger import setup_logger
from app.services.auth_service import login_user
from app.schemas.auth import Token

logger = setup_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка входа пользователя: {user_data.username}")

        result = await login_user(db, user_data.username, user_data.password)

        return result

    except Exception as e:
        logger.error(f"Ошибка при входе пользователя {user_data.username}: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Login error: {str(e)}",
            payload=None
        )


@router.get("/me", response_model=DefaultResponse)
async def read_users_me(current_user: dict = Depends(get_current_user_optional)):
    try:
        if not current_user:
            logger.debug("Запрос информации о пользователе: пользователь не аутентифицирован")
            return DefaultResponse(
                error=True,
                message="User not authenticated",
                payload=None
            )

        logger.debug(f"Запрос информации о пользователе: {current_user.username} (ID: {current_user.id})")

        return DefaultResponse(
            error=False,
            message="Success",
            payload=current_user
        )

    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Error retrieving user info: {str(e)}",
            payload=None
        )