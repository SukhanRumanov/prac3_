from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentSchema, DepartmentCreate, DepartmentUpdate
from app.api.dependencies import get_current_user_optional, get_current_superuser

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=list[DepartmentSchema])
async def get_departments(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    result = await db.execute(
        select(
            Department,
            func.count(Employee.id).label('employee_count')
        )
        .outerjoin(Employee, Department.id == Employee.department_id)
        .group_by(Department.id)
        .offset(skip)
        .limit(limit)
    )
    departments_with_count = result.all()

    departments = []
    for dept, emp_count in departments_with_count:
        departments.append(DepartmentSchema(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            employee_count=emp_count
        ))

    return departments


@router.get("/{department_id}", response_model=DepartmentSchema)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    """Получить отдел по ID"""
    result = await db.execute(
        select(
            Department,
            func.count(Employee.id).label('employee_count')
        )
        .outerjoin(Employee, Department.id == Employee.department_id)
        .where(Department.id == department_id)
        .group_by(Department.id)
    )
    department_data = result.first()

    if not department_data:
        raise HTTPException(status_code=404, detail="Department not found")

    department, emp_count = department_data
    return DepartmentSchema(
        id=department.id,
        name=department.name,
        description=department.description,
        employee_count=emp_count
    )


@router.post("/", response_model=DepartmentSchema)
async def create_department(
        department_data: DepartmentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    department = Department(**department_data.model_dump())
    db.add(department)
    await db.commit()
    await db.refresh(department)

    return DepartmentSchema(
        id=department.id,
        name=department.name,
        description=department.description,
        employee_count=0
    )


@router.put("/{department_id}", response_model=DepartmentSchema)
async def update_department(
        department_id: int,
        department_data: DepartmentUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    update_data = department_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)

    await db.commit()
    await db.refresh(department)

    result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.department_id == department_id)
    )
    emp_count = result.scalar()

    return DepartmentSchema(
        id=department.id,
        name=department.name,
        description=department.description,
        employee_count=emp_count
    )


@router.delete("/{department_id}")
async def delete_department(
        department_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.department_id == department_id)
    )
    emp_count = result.scalar()

    if emp_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {emp_count} employees"
        )

    await db.delete(department)
    await db.commit()

    return {"message": "Department deleted successfully"}