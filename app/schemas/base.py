from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class DefaultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    error: bool = False
    message: str = "Success"
    payload: Optional[Any] = None


class PaginationParams(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int = 1
    size: int = 100