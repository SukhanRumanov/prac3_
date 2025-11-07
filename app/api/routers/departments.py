from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentSchema, DepartmentCreate, DepartmentUpdate
from app.api.dependencies import get_current_user_optional, get_current_superuser
from app.schemas.base import DefaultResponse

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=DefaultResponse)
async def get_departments(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    try:
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

        return DefaultResponse(
            error=False,
            message="Departments retrieved successfully",
            payload=departments
        )
    except Exception as e:
        return DefaultResponse(
            error=True,
            message=f"Error retrieving departments: {str(e)}",
            payload=None
        )


@router.get("/{department_id}", response_model=DefaultResponse)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    try:
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
            return DefaultResponse(
                error=True,
                message="Department not found",
                payload=None
            )

        department, emp_count = department_data
        department_schema = DepartmentSchema(
            id=department.id,
            name=department.name,
            description=department.description,
            employee_count=emp_count
        )

        return DefaultResponse(
            error=False,
            message="Department retrieved successfully",
            payload=department_schema
        )
    except Exception as e:
        return DefaultResponse(
            error=True,
            message=f"Error retrieving department: {str(e)}",
            payload=None
        )


@router.post("/", response_model=DefaultResponse)
async def create_department(
        department_data: DepartmentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        department = Department(**department_data.model_dump())
        db.add(department)
        await db.commit()
        await db.refresh(department)

        department_schema = DepartmentSchema(
            id=department.id,
            name=department.name,
            description=department.description,
            employee_count=0
        )

        return DefaultResponse(
            error=False,
            message="Department created successfully",
            payload=department_schema
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error creating department: {str(e)}",
            payload=None
        )


@router.put("/{department_id}", response_model=DefaultResponse)
async def update_department(
        department_id: int,
        department_data: DepartmentUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        result = await db.execute(select(Department).where(Department.id == department_id))
        department = result.scalar_one_or_none()

        if not department:
            return DefaultResponse(
                error=True,
                message="Department not found",
                payload=None
            )

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

        department_schema = DepartmentSchema(
            id=department.id,
            name=department.name,
            description=department.description,
            employee_count=emp_count
        )

        return DefaultResponse(
            error=False,
            message="Department updated successfully",
            payload=department_schema
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error updating department: {str(e)}",
            payload=None
        )


@router.delete("/{department_id}", response_model=DefaultResponse)
async def delete_department(
        department_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        result = await db.execute(select(Department).where(Department.id == department_id))
        department = result.scalar_one_or_none()

        if not department:
            return DefaultResponse(
                error=True,
                message="Department not found",
                payload=None
            )

        result = await db.execute(
            select(func.count(Employee.id))
            .where(Employee.department_id == department_id)
        )
        emp_count = result.scalar()

        if emp_count > 0:
            return DefaultResponse(
                error=True,
                message=f"Cannot delete department with {emp_count} employees",
                payload=None
            )

        await db.delete(department)
        await db.commit()

        return DefaultResponse(
            error=False,
            message="Department deleted successfully",
            payload=None
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error deleting department: {str(e)}",
            payload=None
        )