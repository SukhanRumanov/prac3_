from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, Union
import secrets
import hashlib

from app.db.session import get_db
from app.models.user import User
from app.schemas.base import DefaultResponse
from fastapi.responses import RedirectResponse
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.logger.logger import setup_logger

logger = setup_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        logger.debug("Начало проверки пароля")
        new_hash = get_password_hash(plain_password)
        result = secrets.compare_digest(new_hash, hashed_password)
        logger.debug(f"Результат проверки пароля: {'успешно' if result else 'неудачно'}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке пароля: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    try:
        logger.debug("Генерация хеша пароля")
        salt = "fixed_salt_here"
        hash_result = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        logger.debug("Хеш пароля успешно сгенерирован")
        return hash_result
    except Exception as e:
        logger.error(f"Ошибка при генерации хеша пароля: {str(e)}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        logger.debug(f"Создание access token для пользователя: {data.get('sub')}")
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Access token успешно создан для пользователя: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Ошибка при создании access token: {str(e)}")
        raise


def verify_token(token: str) -> dict:
    try:
        logger.debug("Начало проверки токена")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        is_superuser: bool = payload.get("is_superuser", False)

        if username is None:
            logger.warning("Невалидный токен: отсутствует subject")
            raise JWTError("Invalid token: no subject")

        logger.debug(f"Токен успешно проверен для пользователя: {username}, суперпользователь: {is_superuser}")
        return {"username": username, "is_superuser": is_superuser}

    except JWTError as e:
        logger.warning(f"Ошибка проверки токена: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Union[User, DefaultResponse]:
    try:
        logger.info(f"Начало аутентификации пользователя: {username}")
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

        logger.info(f"Пользователь успешно аутентифицирован: {username}")
        return user

    except Exception as e:
        logger.error(f"Ошибка аутентификации пользователя {username}: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Authentication error: {str(e)}",
            payload=None
        )


async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    try:
        logger.debug("Получение текущего пользователя из токена")
        token = request.cookies.get("access_token")
        if not token:
            logger.debug("Токен не найден в cookies")
            return None

        payload = verify_token(token)
        username = payload.get("username")

        if not username:
            logger.warning("Токен не содержит username")
            return None

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"Пользователь не найден в базе данных: {username}")
            return None

        if not user.is_active:
            logger.warning(f"Пользователь неактивен: {username}")
            return None

        logger.debug(f"Текущий пользователь получен: {username}")
        return user

    except (JWTError, HTTPException) as e:
        logger.warning(f"Ошибка JWT при получении текущего пользователя: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении текущего пользователя: {str(e)}")
        return None


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    logger.debug("Получение текущего пользователя (опционально)")
    return await get_current_user(request, db)


async def get_current_superuser(
        current_user: User = Depends(get_current_user)
) -> Union[User, DefaultResponse]:
    logger.debug("Проверка прав суперпользователя")

    if current_user is None:
        logger.warning("Попытка доступа к админ-функции без аутентификации")
        return DefaultResponse(
            error=True,
            message="Authentication required",
            payload=None
        )

    if not current_user.is_superuser:
        logger.warning(f"Попытка доступа к админ-функции без прав: {current_user.username}")
        return DefaultResponse(
            error=True,
            message="Admin access required",
            payload=None
        )

    logger.debug(f"Доступ к админ-функции разрешен для: {current_user.username}")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    logger.debug("Проверка прав администратора")

    if current_user is None:
        logger.warning("Редирект на логин: пользователь не аутентифицирован")
        raise HTTPException(
            status_code=307,
            detail="Not authenticated",
            headers={"Location": "/web/login"}
        )

    if not current_user.is_superuser:
        logger.warning(f"Редирект на главную: недостаточно прав для пользователя {current_user.username}")
        raise HTTPException(
            status_code=307,
            detail="Admin access required",
            headers={"Location": "/web/"}
        )

    logger.debug(f"Права администратора подтверждены для: {current_user.username}")
    return current_user


def create_user_access_token(user: User) -> str:
    try:
        logger.debug(f"Создание access token для пользователя: {user.username}")
        data = {
            "sub": user.username,
            "is_superuser": user.is_superuser,
            "user_id": str(user.id)
        }
        token = create_access_token(data)
        logger.debug(f"Access token создан для пользователя: {user.username}")
        return token
    except Exception as e:
        logger.error(f"Ошибка создания access token для пользователя {user.username}: {str(e)}")
        raise


async def login_user(db: AsyncSession, username: str, password: str) -> Union[User, DefaultResponse]:
    logger.info(f"Начало процесса логина для пользователя: {username}")
    user = await authenticate_user(db, username, password)

    if isinstance(user, DefaultResponse):
        logger.warning(f"Логин неудачен для пользователя: {username}")
        return user

    access_token = create_user_access_token(user)
    logger.info(f"Логин успешен для пользователя: {username}")
    return user


def create_login_response(user: User, redirect_url: str = "/web/") -> RedirectResponse:
    try:
        logger.info(f"Создание ответа логина для пользователя: {user.username}")
        access_token = create_user_access_token(user)

        response = RedirectResponse(url=redirect_url, status_code=303)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )

        logger.info(f"Ответ логина создан, редирект на: {redirect_url}")
        return response
    except Exception as e:
        logger.error(f"Ошибка создания ответа логина для пользователя {user.username}: {str(e)}")
        raise


async def logout_user() -> RedirectResponse:
    try:
        logger.info("Выход пользователя из системы")
        response = RedirectResponse(url="/web/login", status_code=303)
        response.delete_cookie(key="access_token")
        logger.info("Пользователь успешно вышел из системы")
        return response
    except Exception as e:
        logger.error(f"Ошибка при выходе пользователя: {str(e)}")
        raise