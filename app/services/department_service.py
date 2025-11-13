# services/department_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Tuple
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentSchema, DepartmentCreate, DepartmentUpdate
from app.schemas.base import DefaultResponse
import logging

logger = logging.getLogger(__name__)


class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_departments(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> DefaultResponse:
        try:
            logger.info(f"Запрос на получение списка отделов (skip: {skip}, limit: {limit})")

            result = await self.db.execute(
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

    async def get_department_by_id(self, department_id: int) -> DefaultResponse:
        try:
            logger.info(f"Запрос на получение отдела с ID: {department_id}")

            result = await self.db.execute(
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

    async def create_department(self, department_data: DepartmentCreate) -> DefaultResponse:
        try:
            logger.info(f"Запрос на создание нового отдела: {department_data.name}")
            logger.debug(f"Данные для создания отдела: {department_data.model_dump()}")

            existing_result = await self.db.execute(
                select(Department).where(Department.name == department_data.name)
            )
            existing_department = existing_result.scalar_one_or_none()

            if existing_department:
                logger.warning(f"Отдел с именем '{department_data.name}' уже существует")
                return DefaultResponse(
                    error=True,
                    message="Department with this name already exists",
                    payload=None
                )

            department = Department(**department_data.model_dump())
            self.db.add(department)
            await self.db.commit()
            await self.db.refresh(department)

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
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error creating department: {str(e)}",
                payload=None
            )

    async def update_department(
            self,
            department_id: int,
            department_data: DepartmentUpdate
    ) -> DefaultResponse:
        try:
            logger.info(f"Запрос на обновление отдела с ID: {department_id}")
            logger.debug(f"Данные для обновления: {department_data.model_dump(exclude_unset=True)}")

            result = await self.db.execute(select(Department).where(Department.id == department_id))
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

            if 'name' in update_data:
                existing_result = await self.db.execute(
                    select(Department).where(
                        Department.name == update_data['name'],
                        Department.id != department_id
                    )
                )
                existing_department = existing_result.scalar_one_or_none()

                if existing_department:
                    logger.warning(f"Отдел с именем '{update_data['name']}' уже существует")
                    return DefaultResponse(
                        error=True,
                        message="Department with this name already exists",
                        payload=None
                    )

            for field, value in update_data.items():
                setattr(department, field, value)

            await self.db.commit()
            await self.db.refresh(department)

            result = await self.db.execute(
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
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error updating department: {str(e)}",
                payload=None
            )

    async def delete_department(self, department_id: int) -> DefaultResponse:
        """
        Удалить департамент
        """
        try:
            logger.info(f"Запрос на удаление отдела с ID: {department_id}")

            result = await self.db.execute(select(Department).where(Department.id == department_id))
            department = result.scalar_one_or_none()

            if not department:
                logger.warning(f"Отдел с ID {department_id} не найден для удаления")
                return DefaultResponse(
                    error=True,
                    message="Department not found",
                    payload=None
                )

            result = await self.db.execute(
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

            await self.db.delete(department)
            await self.db.commit()

            logger.info(f"Успешно удален отдел: {department.name} (ID: {department_id})")
            return DefaultResponse(
                error=False,
                message="Department deleted successfully",
                payload=None
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении отдела с ID {department_id}: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error deleting department: {str(e)}",
                payload=None
            )

    async def get_departments_for_web(self) -> List[dict]:
        """
        Получить департаменты для веб-интерфейса
        """
        try:
            result = await self.db.execute(select(Department))
            departments = result.scalars().all()

            departments_data = []
            for dept in departments:
                employee_count_result = await self.db.execute(
                    select(func.count(Employee.id)).where(Employee.department_id == dept.id)
                )
                employee_count = employee_count_result.scalar()

                department_schema = DepartmentSchema(
                    id=dept.id,
                    name=dept.name,
                    description=dept.description,
                    employee_count=employee_count
                )

                departments_data.append({
                    "id": department_schema.id,
                    "name": department_schema.name,
                    "description": department_schema.description,
                    "employee_count": department_schema.employee_count
                })
                logger.info(f"{department_schema.name} - {department_schema.description}")

            return departments_data
        except Exception as e:
            logger.error(f"Ошибка при получении отделов для веб-интерфейса: {str(e)}")
            return []