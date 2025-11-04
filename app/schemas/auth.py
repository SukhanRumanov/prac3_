from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserLogin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str


class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str


class TokenData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: Optional[str] = None


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_superuser: bool