from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class EmployeeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    birth_date: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hire_date: date
    salary: Decimal
    rate: float = 1.0
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status_id: int = 1
    address: Optional[str] = None


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    birth_date: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hire_date: date
    salary: Decimal
    rate: float = 1.0
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status_id: int = 1
    address: Optional[str] = None


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hire_date: Optional[date] = None
    salary: Optional[Decimal] = None
    rate: Optional[float] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status_id: Optional[int] = None
    address: Optional[str] = None


class EmployeeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[EmployeeSchema]
    total: int
    page: int
    size: int
    pages: int


class EmployeeFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status_id: Optional[int] = None
    hire_date_from: Optional[date] = None
    hire_date_to: Optional[date] = None
    salary_from: Optional[Decimal] = None
    salary_to: Optional[Decimal] = None
    search: Optional[str] = None