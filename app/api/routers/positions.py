from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.position import PositionCreate, PositionUpdate
from app.core.security import get_current_active_user, get_current_superuser
from app.schemas.base import DefaultResponse
from app.services.position_service import PositionService
from app.models.user import User

router = APIRouter(prefix="/positions", tags=["positions"])

@router.get("/", response_model=DefaultResponse)
async def get_positions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = PositionService(db)
    return await service.get_all_positions(skip, limit)

@router.get("/{position_id}", response_model=DefaultResponse)
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = PositionService(db)
    return await service.get_position_by_id(position_id)

@router.post("/", response_model=DefaultResponse)
async def create_position(
    position_data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = PositionService(db)
    return await service.create_position(position_data)

@router.put("/{position_id}", response_model=DefaultResponse)
async def update_position(
    position_id: int,
    position_data: PositionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = PositionService(db)
    return await service.update_position(position_id, position_data)

@router.delete("/{position_id}", response_model=DefaultResponse)
async def delete_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = PositionService(db)
    return await service.delete_position(position_id)