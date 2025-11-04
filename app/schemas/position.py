from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PositionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    base_salary: Decimal
    employee_count: Optional[int] = 0


class PositionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: Optional[str] = None
    base_salary: Decimal


class PositionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    description: Optional[str] = None
    base_salary: Optional[Decimal] = None


class PositionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[PositionSchema]
    total: int