from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DepartmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    employee_count: Optional[int] = 0


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[DepartmentSchema]
    total: int