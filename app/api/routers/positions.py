from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.position import Position
from app.models.employee import Employee
from app.schemas.position import PositionSchema, PositionCreate, PositionUpdate
from app.api.dependencies import get_current_user_optional, get_current_superuser

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=list[PositionSchema])
async def get_positions(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
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

    return positions


@router.get("/{position_id}", response_model=PositionSchema)
async def get_position(position_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Position not found")

    position, emp_count = position_data
    return PositionSchema(
        id=position.id,
        title=position.title,
        description=position.description,
        base_salary=position.base_salary,
        employee_count=emp_count
    )


@router.post("/", response_model=PositionSchema)
async def create_position(
        position_data: PositionCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    """Создать новую должность"""
    position = Position(**position_data.model_dump())
    db.add(position)
    await db.commit()
    await db.refresh(position)

    return PositionSchema(
        id=position.id,
        title=position.title,
        description=position.description,
        base_salary=position.base_salary,
        employee_count=0
    )


@router.put("/{position_id}", response_model=PositionSchema)
async def update_position(
        position_id: int,
        position_data: PositionUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    update_data = position_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(position, field, value)

    await db.commit()
    await db.refresh(position)

    # Получаем количество сотрудников
    result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.position_id == position_id)
    )
    emp_count = result.scalar()

    return PositionSchema(
        id=position.id,
        title=position.title,
        description=position.description,
        base_salary=position.base_salary,
        employee_count=emp_count
    )


@router.delete("/{position_id}")
async def delete_position(
        position_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    """Удалить должность"""
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Проверяем есть ли сотрудники с этой должностью
    result = await db.execute(
        select(func.count(Employee.id))
        .where(Employee.position_id == position_id)
    )
    emp_count = result.scalar()

    if emp_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete position with {emp_count} employees"
        )

    await db.delete(position)
    await db.commit()

    return {"message": "Position deleted successfully"}