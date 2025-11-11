from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routers import employees, departments, positions, auth
from app.api.routers.router_web.web import router as web_router
import uvicorn
from app.logger.logger import setup_logger
from app.db.init_db import init_db
import asyncio

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована")
    yield
    logger.info("Приложение останавливается...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Employee Management System API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(departments.router)
app.include_router(positions.router)
app.include_router(auth.router)
app.include_router(web_router)

@app.get("/")
async def root():
    logger.info("Запрос к корневому эндпоинту")
    return {
        "message": "Employee Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    logger.debug("Проверка здоровья приложения")
    return {"status": "healthy", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    logger.info("Запуск сервера Uvicorn")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )