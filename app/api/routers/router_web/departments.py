from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user
from app.services.department_service import DepartmentService
from fastapi.templating import Jinja2Templates

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

    service = DepartmentService(db)
    departments_data = await service.get_departments_for_web()

    return templates.TemplateResponse("departments.html", {
        "request": request,
        "departments": departments_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })