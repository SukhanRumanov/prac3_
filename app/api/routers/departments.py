from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.core.security import get_current_active_user, get_current_superuser
from app.schemas.base import DefaultResponse
from app.services.department_service import DepartmentService
from app.models.user import User

router = APIRouter(prefix="/departments", tags=["departments"])

@router.get("/", response_model=DefaultResponse)
async def get_departments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = DepartmentService(db)
    return await service.get_all_departments(skip, limit)

@router.get("/{department_id}", response_model=DefaultResponse)
async def get_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = DepartmentService(db)
    return await service.get_department_by_id(department_id)

@router.post("/", response_model=DefaultResponse)
async def create_department(
    department_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = DepartmentService(db)
    return await service.create_department(department_data)

@router.put("/{department_id}", response_model=DefaultResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = DepartmentService(db)
    return await service.update_department(department_id, department_data)

@router.delete("/{department_id}", response_model=DefaultResponse)
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = DepartmentService(db)
    return await service.delete_department(department_id)