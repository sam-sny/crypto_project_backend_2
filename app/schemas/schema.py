from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    profile_image: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_google_user: bool

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    email: str
    password: str
