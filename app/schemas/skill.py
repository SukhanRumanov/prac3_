from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    employee_count: Optional[int] = 0


class SkillListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[SkillSchema]
    total: int