from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user


async def get_db_session(db: AsyncSession = Depends(get_db)):
    return db


async def get_current_user_optional():
    return {"username": "user", "is_superuser": False}


async def get_current_superuser():
    return {"username": "admin", "is_superuser": True}