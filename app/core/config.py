from pydantic import BaseModel


class Settings(BaseModel):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:@localhost:5432/employee_db"


    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    PROJECT_NAME: str = "Employee Management System"
    DEBUG: bool = True

settings = Settings()