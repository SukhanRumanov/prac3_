from fastapi import APIRouter, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.core.security import get_current_user
from app.schemas.department import DepartmentSchema

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()
from app.logger.logger import setup_logger

logger = setup_logger(__name__)
@router.get("/departments")
async def web_departments(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

    result = await db.execute(select(Department))
    departments = result.scalars().all()

    departments_data = []
    for dept in departments:
        employee_count_result = await db.execute(
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

    return templates.TemplateResponse("departments.html", {
        "request": request,
        "departments": departments_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })
