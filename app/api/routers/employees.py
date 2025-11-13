# api/employees.py
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.core.security import get_current_active_user, get_current_superuser
from app.schemas.base import DefaultResponse
from app.services.employee_service import EmployeeService
from app.models.user import User

router = APIRouter(prefix="/employees", tags=["employees"])

@router.get("/", response_model=DefaultResponse)
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    position_id: Optional[int] = None,
    status_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = EmployeeService(db)
    return await service.get_all_employees(
        skip=skip,
        limit=limit,
        department_id=department_id,
        position_id=position_id,
        status_id=status_id,
        search=search
    )

@router.get("/{employee_id}", response_model=DefaultResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = EmployeeService(db)
    return await service.get_employee_by_id(employee_id)

@router.post("/", response_model=DefaultResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = EmployeeService(db)
    return await service.create_employee(employee_data)

@router.put("/{employee_id}", response_model=DefaultResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = EmployeeService(db)
    return await service.update_employee(employee_id, employee_data)

@router.delete("/{employee_id}", response_model=DefaultResponse)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    service = EmployeeService(db)
    return await service.delete_employee(employee_id)