from pydantic import BaseModel


class Settings(BaseModel):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5432/employee_db"


    SECRET_KEY: str = "123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    PROJECT_NAME: str = "Employee Management System"
    DEBUG: bool = True

settings = Settings()