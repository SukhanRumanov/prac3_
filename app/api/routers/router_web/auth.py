from fastapi import APIRouter, Request, Depends, Form, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import (
    get_current_user,
    authenticate_user,
    get_password_hash,
    create_user_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.schemas.base import DefaultResponse

from app.logger.logger import setup_logger
from app.services.auth_service import login_user

logger = setup_logger(__name__)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    logger.debug("Запрос страницы входа")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Попытка входа пользователя: {username}")

        result = await login_user(db, username, password)

        if isinstance(result, DefaultResponse):
            logger.warning(f"Неудачная попытка входа пользователя {username}: {result.message}")
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": result.message
            })

        response = RedirectResponse(url="/web/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=result.access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )

        logger.info(f"Успешный вход пользователя: {username}")
        return response

    except Exception as e:
        logger.error(f"Ошибка при входе пользователя {username}: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Login error occurred"
        })

@router.get("/register")
async def register_page(request: Request):
    logger.debug("Запрос страницы регистрации")
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Попытка регистрации пользователя: {username}, email: {email}")

        if password != confirm_password:
            logger.warning(f"Пароли не совпадают при регистрации пользователя: {username}")
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Passwords do not match"
            })

        existing_user = await db.execute(select(User).where(User.username == username))
        if existing_user.scalar_one_or_none():
            logger.warning(f"Попытка регистрации с существующим именем пользователя: {username}")
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Username already exists"
            })

        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            logger.warning(f"Попытка регистрации с существующим email: {email}")
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Email already exists"
            })

        hashed_password = get_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        access_token = create_user_access_token(new_user)

        response = RedirectResponse(url="/web/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )

        logger.info(f"Успешная регистрация пользователя: {username} (ID: {new_user.id})")
        return response

    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя {username}: {str(e)}")
        await db.rollback()
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Registration failed: {str(e)}"
        })


@router.post("/logout")
async def logout():
    logger.info("Запрос выхода из системы (POST)")
    response = RedirectResponse(url="/web/login", status_code=302)
    response.delete_cookie(key="access_token")
    logger.debug("Удален cookie access_token")
    return response


@router.get("/logout")
async def logout(response: Response):
    logger.info("Запрос выхода из системы (GET)")
    response = RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="user")
    logger.debug("Удален cookie user")
    return response


@router.get("/")
async def web_root(
        request: Request,
        current_user=Depends(get_current_user)
):
    try:
        if current_user is None:
            logger.debug("Доступ к корневой странице: пользователь не аутентифицирован, редирект на логин")
            return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

        logger.debug(
            f"Доступ к корневой странице: пользователь {current_user.username} (ID: {current_user.id}), админ: {current_user.is_superuser}")

        return templates.TemplateResponse("index.html", {
            "request": request,
            "current_user": current_user,
            "is_admin": current_user.is_superuser
        })

    except Exception as e:
        logger.error(f"Ошибка при загрузке корневой страницы: {str(e)}")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)