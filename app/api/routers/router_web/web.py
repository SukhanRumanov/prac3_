from fastapi import APIRouter
from app.api.routers.router_web.auth import router as auth_router
from app.api.routers.router_web.employees import router as employees_router
from app.api.routers.router_web.departments import router as departments_router
from app.api.routers.router_web.positions import router as positions_router
from app.api.routers.router_web.edit import router as edit_router

router = APIRouter(prefix="/web", tags=["web"])

router.include_router(auth_router)
router.include_router(employees_router)
router.include_router(departments_router)
router.include_router(positions_router)
router.include_router(edit_router)

__all__ = ["router"]