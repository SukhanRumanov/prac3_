from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal

from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.models.skill import Skill
from app.schemas.employee import EmployeeSchema, EmployeeCreate, EmployeeUpdate
from app.schemas.base import DefaultResponse
import logging

logger = logging.getLogger(__name__)


class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _build_employee_query(self, filters: Dict[str, Any] = None):
        query = select(Employee).options(
            selectinload(Employee.department),
            selectinload(Employee.position),
            selectinload(Employee.status),
            selectinload(Employee.skills)
        )

        if filters:
            if filters.get('department_id'):
                query = query.where(Employee.department_id == filters['department_id'])
            if filters.get('position_id'):
                query = query.where(Employee.position_id == filters['position_id'])
            if filters.get('status_id'):
                query = query.where(Employee.status_id == filters['status_id'])
            if filters.get('search'):
                search_filter = or_(
                    Employee.first_name.ilike(f"%{filters['search']}%"),
                    Employee.last_name.ilike(f"%{filters['search']}%"),
                    Employee.middle_name.ilike(f"%{filters['search']}%")
                )
                query = query.where(search_filter)

        return query

    async def get_all_employees(
            self,
            skip: int = 0,
            limit: int = 100,
            department_id: Optional[int] = None,
            position_id: Optional[int] = None,
            status_id: Optional[int] = None,
            search: Optional[str] = None
    ) -> DefaultResponse:
        try:
            logger.info(
                f"Запрос сотрудников (skip: {skip}, limit: {limit}, "
                f"department_id: {department_id}, position_id: {position_id}, "
                f"status_id: {status_id}, search: '{search}')"
            )

            filters = {
                'department_id': department_id,
                'position_id': position_id,
                'status_id': status_id,
                'search': search
            }

            query = await self._build_employee_query(filters)
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
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

            logger.info(f"Получено {len(employee_schemas)} сотрудников")
            return DefaultResponse(
                error=False,
                message="Employees retrieved successfully",
                payload=employee_schemas
            )
        except Exception as e:
            logger.error(f"Ошибка получения сотрудников: {str(e)}")
            return DefaultResponse(
                error=True,
                message=f"Error retrieving employees: {str(e)}",
                payload=None
            )

    async def get_employee_by_id(self, employee_id: int) -> DefaultResponse:
        try:
            logger.info(f"Запрос сотрудника с ID: {employee_id}")

            query = await self._build_employee_query()
            query = query.where(Employee.id == employee_id)

            result = await self.db.execute(query)
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

            logger.info(f"Получен сотрудник: {employee.full_name} (ID: {employee.id})")
            return DefaultResponse(
                error=False,
                message="Employee retrieved successfully",
                payload=employee_schema
            )
        except Exception as e:
            logger.error(f"Ошибка получения сотрудника с ID {employee_id}: {str(e)}")
            return DefaultResponse(
                error=True,
                message=f"Error retrieving employee: {str(e)}",
                payload=None
            )

    async def create_employee(self, employee_data: EmployeeCreate) -> DefaultResponse:
        try:
            logger.info(f"Создание сотрудника: {employee_data.first_name} {employee_data.last_name}")

            validation_result = await self._validate_employee_relations(employee_data)
            if validation_result:
                return validation_result

            employee = Employee(**employee_data.model_dump())
            self.db.add(employee)
            await self.db.commit()
            await self.db.refresh(employee)

            result = await self.get_employee_by_id(employee.id)

            logger.info(f"Создан сотрудник: {employee.full_name} (ID: {employee.id})")
            return DefaultResponse(
                error=False,
                message="Employee created successfully",
                payload=result.payload
            )

        except Exception as e:
            logger.error(f"Ошибка создания сотрудника: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error creating employee: {str(e)}",
                payload=None
            )

    async def update_employee(self, employee_id: int, employee_data: EmployeeUpdate) -> DefaultResponse:
        try:
            logger.info(f"Обновление сотрудника с ID: {employee_id}")

            result = await self.db.execute(
                select(Employee).where(Employee.id == employee_id)
            )
            employee = result.scalar_one_or_none()

            if not employee:
                logger.warning(f"Сотрудник с ID {employee_id} не найден")
                return DefaultResponse(
                    error=True,
                    message="Employee not found",
                    payload=None
                )

            update_data = employee_data.model_dump(exclude_unset=True)
            validation_result = await self._validate_employee_update_relations(update_data)
            if validation_result:
                return validation_result

            for field, value in update_data.items():
                setattr(employee, field, value)

            await self.db.commit()
            await self.db.refresh(employee)

            result = await self.get_employee_by_id(employee_id)

            logger.info(f"Обновлен сотрудник: {employee.full_name} (ID: {employee.id})")
            return DefaultResponse(
                error=False,
                message="Employee updated successfully",
                payload=result.payload
            )

        except Exception as e:
            logger.error(f"Ошибка обновления сотрудника с ID {employee_id}: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error updating employee: {str(e)}",
                payload=None
            )

    async def delete_employee(self, employee_id: int) -> DefaultResponse:
        try:
            logger.info(f"Удаление сотрудника с ID: {employee_id}")

            result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
            employee = result.scalar_one_or_none()

            if not employee:
                logger.warning(f"Сотрудник с ID {employee_id} не найден")
                return DefaultResponse(
                    error=True,
                    message="Employee not found",
                    payload=None
                )

            await self.db.delete(employee)
            await self.db.commit()

            logger.info(f"Удален сотрудник: {employee.full_name} (ID: {employee_id})")
            return DefaultResponse(
                error=False,
                message="Employee deleted successfully",
                payload=None
            )
        except Exception as e:
            logger.error(f"Ошибка удаления сотрудника с ID {employee_id}: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error deleting employee: {str(e)}",
                payload=None
            )

    async def get_employees_for_web(self) -> List[Dict[str, Any]]:
        try:
            query = select(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.status)
            )

            result = await self.db.execute(query)
            employees = result.unique().scalars().all()

            employee_data = []
            for emp in employees:
                department_name = emp.department.name if emp.department else None
                position_title = emp.position.title if emp.position else None
                status_name = emp.status.name if emp.status else None

                today = date.today()
                age = (today - emp.birth_date).days // 365 if emp.birth_date else None
                work_experience = (today - emp.hire_date).days // 365 if emp.hire_date else None

                employee_data.append({
                    "id": emp.id,
                    "first_name": emp.first_name,
                    "last_name": emp.last_name,
                    "middle_name": emp.middle_name,
                    "birth_date": emp.birth_date,
                    "email": emp.email,
                    "phone": emp.phone,
                    "hire_date": emp.hire_date,
                    "salary": float(emp.salary) if emp.salary else 0.0,
                    "rate": emp.rate,
                    "department_id": emp.department_id,
                    "position_id": emp.position_id,
                    "status_id": emp.status_id,
                    "address": emp.address,
                    "department_name": department_name,
                    "position_title": position_title,
                    "status_name": status_name,
                    "full_name": f"{emp.last_name} {emp.first_name} {emp.middle_name or ''}".strip(),
                    "age": age,
                    "work_experience": work_experience
                })

            logger.info(f"Подготовлено {len(employee_data)} сотрудников для веб-интерфейса")
            return employee_data

        except Exception as e:
            logger.error(f"Ошибка получения сотрудников для веб-интерфейса: {str(e)}")
            return []

    async def _validate_employee_relations(self, employee_data: EmployeeCreate) -> Optional[DefaultResponse]:
        if employee_data.position_id:
            result = await self.db.execute(select(Position).where(Position.id == employee_data.position_id))
            position = result.scalar_one_or_none()
            if not position:
                return DefaultResponse(
                    error=True,
                    message=f"Position with id {employee_data.position_id} not found",
                    payload=None
                )

        if employee_data.department_id:
            result = await self.db.execute(select(Department).where(Department.id == employee_data.department_id))
            department = result.scalar_one_or_none()
            if not department:
                return DefaultResponse(
                    error=True,
                    message=f"Department with id {employee_data.department_id} not found",
                    payload=None
                )

        result = await self.db.execute(select(Status).where(Status.id == employee_data.status_id))
        status = result.scalar_one_or_none()
        if not status:
            return DefaultResponse(
                error=True,
                message=f"Status with id {employee_data.status_id} not found",
                payload=None
            )

        return None

    async def _validate_employee_update_relations(self, update_data: Dict[str, Any]) -> Optional[DefaultResponse]:
        if 'position_id' in update_data and update_data['position_id']:
            result = await self.db.execute(select(Position).where(Position.id == update_data['position_id']))
            position = result.scalar_one_or_none()
            if not position:
                return DefaultResponse(
                    error=True,
                    message=f"Position with id {update_data['position_id']} not found",
                    payload=None
                )

        if 'department_id' in update_data and update_data['department_id']:
            result = await self.db.execute(select(Department).where(Department.id == update_data['department_id']))
            department = result.scalar_one_or_none()
            if not department:
                return DefaultResponse(
                    error=True,
                    message=f"Department with id {update_data['department_id']} not found",
                    payload=None
                )

        if 'status_id' in update_data and update_data['status_id']:
            result = await self.db.execute(select(Status).where(Status.id == update_data['status_id']))
            status = result.scalar_one_or_none()
            if not status:
                return DefaultResponse(
                    error=True,
                    message=f"Status with id {update_data['status_id']} not found",
                    payload=None
                )

        return None