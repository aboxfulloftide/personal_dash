from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RouterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    ssh_port: int = Field(22, ge=1, le=65535)
    ssh_user: str = Field("root", min_length=1, max_length=100)
    ssh_password: Optional[str] = None
    ssh_key: Optional[str] = None
    poll_interval: int = Field(60, ge=10, le=3600)
    script: Optional[str] = None


class RouterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    ssh_user: Optional[str] = Field(None, min_length=1, max_length=100)
    ssh_password: Optional[str] = None
    ssh_key: Optional[str] = None
    poll_interval: Optional[int] = Field(None, ge=10, le=3600)
    script: Optional[str] = None


class RouterResponse(BaseModel):
    id: int
    name: str
    hostname: str
    ssh_port: int
    ssh_user: str
    has_password: bool
    has_key: bool
    poll_interval: int
    script: Optional[str]
    is_online: bool
    ping_ms: Optional[float]
    last_seen: Optional[datetime]
    last_polled: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class RouterPollResultResponse(BaseModel):
    id: int
    router_id: int
    is_online: bool
    ping_ms: Optional[float]
    script_output: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}
