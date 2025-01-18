from pydantic import BaseModel, EmailStr, ConfigDict
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

class UserProfile(UserBase):
    first_name: str  # Ensure this exists in the `user` object
    last_name: str
    username: Optional[str] = None
    profile_image: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserToken(BaseModel):
    token: str