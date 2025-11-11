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
from app.logger.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=DefaultResponse)
async def get_departments(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    try:
        logger.info(f"Запрос на получение списка отделов (skip: {skip}, limit: {limit})")

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

        logger.info(f"Успешно получено {len(departments)} отделов")
        return DefaultResponse(
            error=False,
            message="Departments retrieved successfully",
            payload=departments
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка отделов: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Error retrieving departments: {str(e)}",
            payload=None
        )


@router.get("/{department_id}", response_model=DefaultResponse)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Запрос на получение отдела с ID: {department_id}")

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
            logger.warning(f"Отдел с ID {department_id} не найден")
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

        logger.info(f"Успешно получен отдел: {department.name} (ID: {department.id}), сотрудников: {emp_count}")
        return DefaultResponse(
            error=False,
            message="Department retrieved successfully",
            payload=department_schema
        )
    except Exception as e:
        logger.error(f"Ошибка при получении отдела с ID {department_id}: {str(e)}")
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
        logger.info(f"Запрос на создание нового отдела: {department_data.name}")
        logger.debug(f"Данные для создания отдела: {department_data.model_dump()}")

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

        logger.info(f"Успешно создан новый отдел: {department.name} (ID: {department.id})")
        return DefaultResponse(
            error=False,
            message="Department created successfully",
            payload=department_schema
        )
    except Exception as e:
        logger.error(f"Ошибка при создании отдела '{department_data.name}': {str(e)}")
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
        logger.info(f"Запрос на обновление отдела с ID: {department_id}")
        logger.debug(f"Данные для обновления: {department_data.model_dump(exclude_unset=True)}")

        result = await db.execute(select(Department).where(Department.id == department_id))
        department = result.scalar_one_or_none()

        if not department:
            logger.warning(f"Отдел с ID {department_id} не найден для обновления")
            return DefaultResponse(
                error=True,
                message="Department not found",
                payload=None
            )

        update_data = department_data.model_dump(exclude_unset=True)
        updated_fields = list(update_data.keys())

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

        logger.info(
            f"Успешно обновлен отдел: {department.name} (ID: {department.id}), обновлены поля: {updated_fields}")
        return DefaultResponse(
            error=False,
            message="Department updated successfully",
            payload=department_schema
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении отдела с ID {department_id}: {str(e)}")
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
        logger.info(f"Запрос на удаление отдела с ID: {department_id}")

        result = await db.execute(select(Department).where(Department.id == department_id))
        department = result.scalar_one_or_none()

        if not department:
            logger.warning(f"Отдел с ID {department_id} не найден для удаления")
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
            logger.warning(
                f"Попытка удаления отдела {department.name} (ID: {department_id}) с {emp_count} сотрудниками")
            return DefaultResponse(
                error=True,
                message=f"Cannot delete department with {emp_count} employees",
                payload=None
            )

        await db.delete(department)
        await db.commit()

        logger.info(f"Успешно удален отдел: {department.name} (ID: {department_id})")
        return DefaultResponse(
            error=False,
            message="Department deleted successfully",
            payload=None
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении отдела с ID {department_id}: {str(e)}")
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error deleting department: {str(e)}",
            payload=None
        )