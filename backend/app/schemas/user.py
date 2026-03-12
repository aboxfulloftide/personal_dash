from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = None
    favicon_url: str | None = None


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = None
    favicon_url: str | None = None


class UserResponse(UserBase):
    """Schema for user responses (no sensitive data)."""

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
