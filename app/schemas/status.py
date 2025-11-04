from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class StatusSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    employee_count: Optional[int] = 0


class StatusListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[StatusSchema]
    total: int