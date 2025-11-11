from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.models.skill import Skill
from app.schemas.employee import EmployeeSchema, EmployeeCreate, EmployeeUpdate, EmployeeFilter
from app.api.dependencies import get_current_user_optional, get_current_superuser
from app.schemas.base import DefaultResponse
from app.logger.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=DefaultResponse)
async def get_employees(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        position_id: Optional[int] = None,
        status_id: Optional[int] = None,
        search: Optional[str] = None,
):
    try:
        logger.info(
            f"Запрос на получение списка сотрудников (skip: {skip}, limit: {limit}, "
            f"department_id: {department_id}, position_id: {position_id}, "
            f"status_id: {status_id}, search: '{search}')"
        )

        query = select(Employee).options(
            selectinload(Employee.department),
            selectinload(Employee.position),
            selectinload(Employee.status),
            selectinload(Employee.skills)
        )

        if department_id:
            query = query.where(Employee.department_id == department_id)
            logger.debug(f"Применен фильтр по отделу: {department_id}")
        if position_id:
            query = query.where(Employee.position_id == position_id)
            logger.debug(f"Применен фильтр по должности: {position_id}")
        if status_id:
            query = query.where(Employee.status_id == status_id)
            logger.debug(f"Применен фильтр по статусу: {status_id}")
        if search:
            search_filter = or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.last_name.ilike(f"%{search}%"),
                Employee.middle_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            logger.debug(f"Применен поисковый фильтр: '{search}'")

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        employees = result.scalars().all()

        employee_schemas = []
        for emp in employees:
            schema_data = {
                'id': emp.id,
                'first_name': emp.first_name,
                'last_name': emp.last_name,
                'middle_name': emp.middle_name,
                'birth_date': emp.birth_date,
                'email': emp.email,
                'phone': emp.phone,
                'hire_date': emp.hire_date,
                'salary': emp.salary,
                'rate': emp.rate,
                'department_id': emp.department_id,
                'position_id': emp.position_id,
                'status_id': emp.status_id,
                'address': emp.address,
                'full_name': emp.full_name,
                'created_at': emp.created_at,
                'updated_at': emp.updated_at,
            }

            if emp.department:
                schema_data['department_name'] = emp.department.name
            if emp.position:
                schema_data['position_title'] = emp.position.title
            if emp.status:
                schema_data['status_name'] = emp.status.name
            if emp.skills:
                schema_data['skills'] = [skill.name for skill in emp.skills]

            employee_schemas.append(EmployeeSchema(**schema_data))

        logger.info(f"Успешно получено {len(employee_schemas)} сотрудников")
        return DefaultResponse(
            error=False,
            message="Employees retrieved successfully",
            payload=employee_schemas
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка сотрудников: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Error retrieving employees: {str(e)}",
            payload=None
        )


@router.get("/{employee_id}", response_model=DefaultResponse)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Запрос на получение сотрудника с ID: {employee_id}")

        result = await db.execute(
            select(Employee)
            .options(
                selectinload(Employee.department),
                selectinload(Employee.position),
                selectinload(Employee.status),
                selectinload(Employee.skills)
            )
            .where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            logger.warning(f"Сотрудник с ID {employee_id} не найден")
            return DefaultResponse(
                error=True,
                message="Employee not found",
                payload=None
            )

        schema_data = {
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'middle_name': employee.middle_name,
            'birth_date': employee.birth_date,
            'email': employee.email,
            'phone': employee.phone,
            'hire_date': employee.hire_date,
            'salary': employee.salary,
            'rate': employee.rate,
            'department_id': employee.department_id,
            'position_id': employee.position_id,
            'status_id': employee.status_id,
            'address': employee.address,
            'full_name': employee.full_name,
            'created_at': employee.created_at,
            'updated_at': employee.updated_at,
        }

        if employee.department:
            schema_data['department_name'] = employee.department.name
        if employee.position:
            schema_data['position_title'] = employee.position.title
        if employee.status:
            schema_data['status_name'] = employee.status.name
        if employee.skills:
            schema_data['skills'] = [skill.name for skill in employee.skills]

        employee_schema = EmployeeSchema(**schema_data)

        logger.info(f"Успешно получен сотрудник: {employee.full_name} (ID: {employee.id})")
        return DefaultResponse(
            error=False,
            message="Employee retrieved successfully",
            payload=employee_schema
        )
    except Exception as e:
        logger.error(f"Ошибка при получении сотрудника с ID {employee_id}: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Error retrieving employee: {str(e)}",
            payload=None
        )


@router.post("/", response_model=DefaultResponse)
async def create_employee(
        employee_data: EmployeeCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        logger.info(f"Запрос на создание нового сотрудника: {employee_data.first_name} {employee_data.last_name}")
        logger.debug(f"Данные для создания сотрудника: {employee_data.model_dump(exclude={'password'})}")

        if employee_data.position_id:
            position_result = await db.execute(
                select(Position).where(Position.id == employee_data.position_id)
            )
            position = position_result.scalar_one_or_none()

            if not position:
                logger.warning(f"Позиция с ID {employee_data.position_id} не найдена")
                return DefaultResponse(
                    error=True,
                    message=f"Position with id {employee_data.position_id} not found",
                    payload=None
                )
            logger.debug(f"Найдена позиция: {position.title}")

        if employee_data.department_id:
            department_result = await db.execute(
                select(Department).where(Department.id == employee_data.department_id)
            )
            department = department_result.scalar_one_or_none()
            if not department:
                logger.warning(f"Отдел с ID {employee_data.department_id} не найден")
                return DefaultResponse(
                    error=True,
                    message=f"Department with id {employee_data.department_id} not found",
                    payload=None
                )
            logger.debug(f"Найден отдел: {department.name}")

        status_result = await db.execute(
            select(Status).where(Status.id == employee_data.status_id)
        )
        status = status_result.scalar_one_or_none()
        if not status:
            logger.warning(f"Статус с ID {employee_data.status_id} не найден")
            return DefaultResponse(
                error=True,
                message=f"Status with id {employee_data.status_id} not found",
                payload=None
            )
        logger.debug(f"Найден статус: {status.name}")

        employee = Employee(**employee_data.model_dump())
        db.add(employee)
        await db.commit()
        await db.refresh(employee)

        employee_response = await get_employee(employee.id, db)

        logger.info(f"Успешно создан сотрудник: {employee.full_name} (ID: {employee.id})")
        return DefaultResponse(
            error=False,
            message="Employee created successfully",
            payload=employee_response.payload
        )

    except Exception as e:
        logger.error(f"Ошибка при создании сотрудника {employee_data.first_name} {employee_data.last_name}: {str(e)}")
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error creating employee: {str(e)}",
            payload=None
        )


@router.put("/{employee_id}", response_model=DefaultResponse)
async def update_employee(
        employee_id: int,
        employee_data: EmployeeUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        logger.info(f"Запрос на обновление сотрудника с ID: {employee_id}")
        logger.debug(f"Данные для обновления: {employee_data.model_dump(exclude_unset=True)}")

        result = await db.execute(
            select(Employee)
            .options(
                selectinload(Employee.department),
                selectinload(Employee.position),
                selectinload(Employee.status),
                selectinload(Employee.skills)
            )
            .where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            logger.warning(f"Сотрудник с ID {employee_id} не найден для обновления")
            return DefaultResponse(
                error=True,
                message="Employee not found",
                payload=None
            )

        update_data = employee_data.model_dump(exclude_unset=True)

        if 'position_id' in update_data and update_data['position_id']:
            position_result = await db.execute(
                select(Position).where(Position.id == update_data['position_id'])
            )
            position = position_result.scalar_one_or_none()
            if not position:
                logger.warning(f"Позиция с ID {update_data['position_id']} не найдена")
                return DefaultResponse(
                    error=True,
                    message=f"Position with id {update_data['position_id']} not found",
                    payload=None
                )
            logger.debug(f"Найдена новая позиция: {position.title}")

        if 'department_id' in update_data and update_data['department_id']:
            department_result = await db.execute(
                select(Department).where(Department.id == update_data['department_id'])
            )
            department = department_result.scalar_one_or_none()
            if not department:
                logger.warning(f"Отдел с ID {update_data['department_id']} не найден")
                return DefaultResponse(
                    error=True,
                    message=f"Department with id {update_data['department_id']} not found",
                    payload=None
                )
            logger.debug(f"Найден новый отдел: {department.name}")

        if 'status_id' in update_data and update_data['status_id']:
            status_result = await db.execute(
                select(Status).where(Status.id == update_data['status_id'])
            )
            status = status_result.scalar_one_or_none()
            if not status:
                logger.warning(f"Статус с ID {update_data['status_id']} не найден")
                return DefaultResponse(
                    error=True,
                    message=f"Status with id {update_data['status_id']} not found",
                    payload=None
                )
            logger.debug(f"Найден новый статус: {status.name}")

        for field, value in update_data.items():
            setattr(employee, field, value)
            logger.debug(f"Обновлено поле {field} для сотрудника {employee_id}")

        await db.commit()
        await db.refresh(employee)

        employee_response = await get_employee(employee_id, db)

        logger.info(f"Успешно обновлен сотрудник: {employee.full_name} (ID: {employee.id})")
        return DefaultResponse(
            error=False,
            message="Employee updated successfully",
            payload=employee_response.payload
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении сотрудника с ID {employee_id}: {str(e)}")
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error updating employee: {str(e)}",
            payload=None
        )


@router.delete("/{employee_id}", response_model=DefaultResponse)
async def delete_employee(
        employee_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        logger.info(f"Запрос на удаление сотрудника с ID: {employee_id}")

        result = await db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()

        if not employee:
            logger.warning(f"Сотрудник с ID {employee_id} не найден для удаления")
            return DefaultResponse(
                error=True,
                message="Employee not found",
                payload=None
            )

        await db.delete(employee)
        await db.commit()

        logger.info(f"Успешно удален сотрудник: {employee.full_name} (ID: {employee_id})")
        return DefaultResponse(
            error=False,
            message="Employee deleted successfully",
            payload=None
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении сотрудника с ID {employee_id}: {str(e)}")
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error deleting employee: {str(e)}",
            payload=None
        )


@router.get("/debug/statuses", response_model=DefaultResponse)
async def debug_statuses(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Запрос на получение списка статусов (debug)")

        result = await db.execute(select(Status))
        statuses = result.scalars().all()

        status_list = [{"id": s.id, "name": s.name} for s in statuses]

        logger.info(f"Успешно получено {len(status_list)} статусов")
        return DefaultResponse(
            error=False,
            message="Statuses retrieved successfully",
            payload=status_list
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка статусов: {str(e)}")
        return DefaultResponse(
            error=True,
            message=f"Error retrieving statuses: {str(e)}",
            payload=None
        )