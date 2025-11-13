# web/positions.py
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import get_current_user
from app.services.position_service import PositionService
from app.logger.logger import setup_logger
from fastapi.templating import Jinja2Templates

logger = setup_logger(__name__)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/positions")
async def web_positions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

    try:
        service = PositionService(db)
        positions_data = await service.get_positions_for_web()

        logger.info(f"Успешно выведено {len(positions_data)} должностей через сервис")

        return templates.TemplateResponse("positions.html", {
            "request": request,
            "positions": positions_data,
            "current_user": current_user,
            "is_admin": current_user.is_superuser
        })

    except Exception as e:
        logger.error(f"Ошибка при получении должностей для веб-интерфейса: {str(e)}")
        return templates.TemplateResponse("positions.html", {
            "request": request,
            "positions": [],
            "current_user": current_user,
            "is_admin": current_user.is_superuser,
            "error": "Ошибка при загрузке данных"
        })