from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    username: str
    email: EmailStr
    password: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[UserSchema]
    total: int