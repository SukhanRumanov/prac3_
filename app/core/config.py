from pydantic import BaseModel

SECRET_KEY: str = ""
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

class Settings(BaseModel):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:@postgres:5432/employee_db"
    PROJECT_NAME: str = "Employee Management System"
    DEBUG: bool = True

settings = Settings()