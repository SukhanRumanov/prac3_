from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.position import Position
from app.models.employee import Employee
from app.schemas.position import PositionSchema, PositionCreate, PositionUpdate
from app.api.dependencies import get_current_user_optional, get_current_superuser
from app.schemas.base import DefaultResponse

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=DefaultResponse)
async def get_positions(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    try:
        result = await db.execute(
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

        return DefaultResponse(
            error=False,
            message="Positions retrieved successfully",
            payload=positions
        )
    except Exception as e:
        return DefaultResponse(
            error=True,
            message=f"Error retrieving positions: {str(e)}",
            payload=None
        )


@router.get("/{position_id}", response_model=DefaultResponse)
async def get_position(position_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
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

        return DefaultResponse(
            error=False,
            message="Position retrieved successfully",
            payload=position_schema
        )
    except Exception as e:
        return DefaultResponse(
            error=True,
            message=f"Error retrieving position: {str(e)}",
            payload=None
        )


@router.post("/", response_model=DefaultResponse)
async def create_position(
        position_data: PositionCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        position = Position(**position_data.model_dump())
        db.add(position)
        await db.commit()
        await db.refresh(position)

        position_schema = PositionSchema(
            id=position.id,
            title=position.title,
            description=position.description,
            base_salary=position.base_salary,
            employee_count=0
        )

        return DefaultResponse(
            error=False,
            message="Position created successfully",
            payload=position_schema
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error creating position: {str(e)}",
            payload=None
        )


@router.put("/{position_id}", response_model=DefaultResponse)
async def update_position(
        position_id: int,
        position_data: PositionUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        result = await db.execute(select(Position).where(Position.id == position_id))
        position = result.scalar_one_or_none()

        if not position:
            return DefaultResponse(
                error=True,
                message="Position not found",
                payload=None
            )

        update_data = position_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(position, field, value)

        await db.commit()
        await db.refresh(position)

        result = await db.execute(
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

        return DefaultResponse(
            error=False,
            message="Position updated successfully",
            payload=position_schema
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error updating position: {str(e)}",
            payload=None
        )


@router.delete("/{position_id}", response_model=DefaultResponse)
async def delete_position(
        position_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    try:
        result = await db.execute(select(Position).where(Position.id == position_id))
        position = result.scalar_one_or_none()

        if not position:
            return DefaultResponse(
                error=True,
                message="Position not found",
                payload=None
            )

        result = await db.execute(
            select(func.count(Employee.id))
            .where(Employee.position_id == position_id)
        )
        emp_count = result.scalar()

        if emp_count > 0:
            return DefaultResponse(
                error=True,
                message=f"Cannot delete position with {emp_count} employees",
                payload=None
            )

        await db.delete(position)
        await db.commit()

        return DefaultResponse(
            error=False,
            message="Position deleted successfully",
            payload=None
        )
    except Exception as e:
        await db.rollback()
        return DefaultResponse(
            error=True,
            message=f"Error deleting position: {str(e)}",
            payload=None
        )