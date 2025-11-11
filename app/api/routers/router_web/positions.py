from fastapi import APIRouter, Request, Depends,status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.position import Position
from app.models.employee import Employee
from app.core.security import get_current_user
from app.schemas.position import PositionSchema

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()
from app.logger.logger import setup_logger

logger = setup_logger(__name__)


@router.get("/positions")
async def web_positions(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

    result = await db.execute(select(Position))
    positions = result.scalars().all()

    positions_data = []
    for pos in positions:
        employee_count_result = await db.execute(
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

        positions_data.append({
            "id": position_schema.id,
            "title": position_schema.title,
            "description": position_schema.description,
            "base_salary": float(position_schema.base_salary),
            "employee_count": position_schema.employee_count
        })
        logger.info("вывод всех должностей")

    return templates.TemplateResponse("positions.html", {
        "request": request,
        "positions": positions_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })