from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator
import re

AccessLevel = Literal["none", "viewer", "user", "admin"]


# ---------- App schemas ----------

class AppCreate(BaseModel):
    slug: str
    display_name: str
    description: str | None = None

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("slug must be lowercase letters, digits, or underscores")
        return v


class AppUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AppResponse(BaseModel):
    id: int
    slug: str
    display_name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Access entry schemas ----------

class UserAccessEntry(BaseModel):
    app_id: int
    app_slug: str
    app_name: str
    level: AccessLevel
    granted_at: datetime

    model_config = {"from_attributes": True}


class SetAccessRequest(BaseModel):
    level: AccessLevel


# ---------- Admin user schemas ----------

class AdminUserCreate(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    is_admin: bool = False


class AdminUserUpdate(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    password: str | None = None


class AdminUserResponse(BaseModel):
    id: int
    email: str
    display_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime
    app_access: list[UserAccessEntry] = []

    model_config = {"from_attributes": True}


# ---------- Token verify schemas ----------

class VerifyRequest(BaseModel):
    app_slug: str | None = None
    min_level: AccessLevel = "viewer"


class VerifyResponse(BaseModel):
    valid: bool
    user_id: int
    email: str
    display_name: str | None
    is_admin: bool
    apps: dict[str, str]
    access_level: str | None = None
