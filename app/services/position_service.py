# services/position_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.models.position import Position
from app.models.employee import Employee
from app.schemas.position import PositionSchema, PositionCreate, PositionUpdate
from app.schemas.base import DefaultResponse
import logging

logger = logging.getLogger(__name__)


class PositionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_positions(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> DefaultResponse:
        try:
            logger.info(f"Запрос на получение списка должностей (skip: {skip}, limit: {limit})")

            result = await self.db.execute(
                select(
                    Position,
                    func.count(Employee.id).label('employee_count')
                )
                .outerjoin(Employee, Position.id == Employee.position_id)
                .group_by(Position.id)
                .offset(skip)
                .limit(limit)
            )
            positions_with_count = result.all()

            positions = []
            for pos, emp_count in positions_with_count:
                positions.append(PositionSchema(
                    id=pos.id,
                    title=pos.title,
                    description=pos.description,
                    base_salary=pos.base_salary,
                    employee_count=emp_count
                ))

            logger.info(f"Успешно получено {len(positions)} должностей")
            return DefaultResponse(
                error=False,
                message="Positions retrieved successfully",
                payload=positions
            )
        except Exception as e:
            logger.error(f"Ошибка при получении списка должностей: {str(e)}")
            return DefaultResponse(
                error=True,
                message=f"Error retrieving positions: {str(e)}",
                payload=None
            )

    async def get_position_by_id(self, position_id: int) -> DefaultResponse:
        try:
            logger.info(f"Запрос на получение должности с ID: {position_id}")

            result = await self.db.execute(
                select(
                    Position,
                    func.count(Employee.id).label('employee_count')
                )
                .outerjoin(Employee, Position.id == Employee.position_id)
                .where(Position.id == position_id)
                .group_by(Position.id)
            )
            position_data = result.first()

            if not position_data:
                logger.warning(f"Должность с ID {position_id} не найдена")
                return DefaultResponse(
                    error=True,
                    message="Position not found",
                    payload=None
                )

            position, emp_count = position_data
            position_schema = PositionSchema(
                id=position.id,
                title=position.title,
                description=position.description,
                base_salary=position.base_salary,
                employee_count=emp_count
            )

            logger.info(f"Успешно получена должность: {position.title} (ID: {position.id})")
            return DefaultResponse(
                error=False,
                message="Position retrieved successfully",
                payload=position_schema
            )
        except Exception as e:
            logger.error(f"Ошибка при получении должности с ID {position_id}: {str(e)}")
            return DefaultResponse(
                error=True,
                message=f"Error retrieving position: {str(e)}",
                payload=None
            )

    async def create_position(self, position_data: PositionCreate) -> DefaultResponse:
        try:
            logger.info(f"Запрос на создание новой должности: {position_data.title}")
            logger.debug(f"Данные для создания должности: {position_data.model_dump()}")

            existing_result = await self.db.execute(
                select(Position).where(Position.title == position_data.title)
            )
            existing_position = existing_result.scalar_one_or_none()

            if existing_position:
                logger.warning(f"Должность с названием '{position_data.title}' уже существует")
                return DefaultResponse(
                    error=True,
                    message="Position with this title already exists",
                    payload=None
                )

            position = Position(**position_data.model_dump())
            self.db.add(position)
            await self.db.commit()
            await self.db.refresh(position)

            position_schema = PositionSchema(
                id=position.id,
                title=position.title,
                description=position.description,
                base_salary=position.base_salary,
                employee_count=0
            )

            logger.info(f"Успешно создана новая должность: {position.title} (ID: {position.id})")
            return DefaultResponse(
                error=False,
                message="Position created successfully",
                payload=position_schema
            )
        except Exception as e:
            logger.error(f"Ошибка при создании должности '{position_data.title}': {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error creating position: {str(e)}",
                payload=None
            )

    async def update_position(
            self,
            position_id: int,
            position_data: PositionUpdate
    ) -> DefaultResponse:
        try:
            logger.info(f"Запрос на обновление должности с ID: {position_id}")
            logger.debug(f"Данные для обновления: {position_data.model_dump(exclude_unset=True)}")

            result = await self.db.execute(select(Position).where(Position.id == position_id))
            position = result.scalar_one_or_none()

            if not position:
                logger.warning(f"Должность с ID {position_id} не найдена для обновления")
                return DefaultResponse(
                    error=True,
                    message="Position not found",
                    payload=None
                )

            update_data = position_data.model_dump(exclude_unset=True)

            # Если обновляется название, проверяем уникальность
            if 'title' in update_data:
                existing_result = await self.db.execute(
                    select(Position).where(
                        Position.title == update_data['title'],
                        Position.id != position_id
                    )
                )
                existing_position = existing_result.scalar_one_or_none()

                if existing_position:
                    logger.warning(f"Должность с названием '{update_data['title']}' уже существует")
                    return DefaultResponse(
                        error=True,
                        message="Position with this title already exists",
                        payload=None
                    )

            for field, value in update_data.items():
                setattr(position, field, value)

            await self.db.commit()
            await self.db.refresh(position)

            result = await self.db.execute(
                select(func.count(Employee.id))
                .where(Employee.position_id == position_id)
            )
            emp_count = result.scalar()

            position_schema = PositionSchema(
                id=position.id,
                title=position.title,
                description=position.description,
                base_salary=position.base_salary,
                employee_count=emp_count
            )

            logger.info(f"Успешно обновлена должность: {position.title} (ID: {position.id})")
            return DefaultResponse(
                error=False,
                message="Position updated successfully",
                payload=position_schema
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении должности с ID {position_id}: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error updating position: {str(e)}",
                payload=None
            )

    async def delete_position(self, position_id: int) -> DefaultResponse:
        try:
            logger.info(f"Запрос на удаление должности с ID: {position_id}")

            result = await self.db.execute(select(Position).where(Position.id == position_id))
            position = result.scalar_one_or_none()

            if not position:
                logger.warning(f"Должность с ID {position_id} не найдена для удаления")
                return DefaultResponse(
                    error=True,
                    message="Position not found",
                    payload=None
                )

            result = await self.db.execute(
                select(func.count(Employee.id))
                .where(Employee.position_id == position_id)
            )
            emp_count = result.scalar()

            if emp_count > 0:
                logger.warning(
                    f"Попытка удаления должности {position.title} (ID: {position_id}) с {emp_count} сотрудниками")
                return DefaultResponse(
                    error=True,
                    message=f"Cannot delete position with {emp_count} employees",
                    payload=None
                )

            await self.db.delete(position)
            await self.db.commit()

            logger.info(f"Успешно удалена должность: {position.title} (ID: {position_id})")
            return DefaultResponse(
                error=False,
                message="Position deleted successfully",
                payload=None
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении должности с ID {position_id}: {str(e)}")
            await self.db.rollback()
            return DefaultResponse(
                error=True,
                message=f"Error deleting position: {str(e)}",
                payload=None
            )

    async def get_positions_for_web(self) -> List[Dict[str, Any]]:
        try:
            result = await self.db.execute(select(Position))
            positions = result.scalars().all()

            positions_data = []
            for pos in positions:
                employee_count_result = await self.db.execute(
                    select(func.count(Employee.id)).where(Employee.position_id == pos.id)
                )
                employee_count = employee_count_result.scalar()

                position_schema = PositionSchema(
                    id=pos.id,
                    title=pos.title,
                    description=pos.description,
                    base_salary=pos.base_salary,
                    employee_count=employee_count
                )

                positions_data.append(position_schema)

            logger.info(f"Успешно подготовлено {len(positions_data)} должностей для веб-интерфейса")
            return positions_data

        except Exception as e:
            logger.error(f"Ошибка при получении должностей для веб-интерфейса: {str(e)}")
            return []