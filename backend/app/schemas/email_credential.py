from pydantic import BaseModel, EmailStr
from datetime import datetime


class EmailCredentialBase(BaseModel):
    imap_server: str
    imap_port: int = 993
    email_address: EmailStr
    enabled: bool = True
    scan_interval_hours: int = 6
    days_to_scan: int = 30


class EmailCredentialCreate(EmailCredentialBase):
    password: str  # Plain password, will be encrypted before storage


class EmailCredentialUpdate(BaseModel):
    imap_server: str | None = None
    imap_port: int | None = None
    email_address: EmailStr | None = None
    password: str | None = None  # Plain password, will be encrypted before storage
    enabled: bool | None = None
    scan_interval_hours: int | None = None
    days_to_scan: int | None = None


class EmailCredentialResponse(EmailCredentialBase):
    id: int
    user_id: int
    last_scan_at: datetime | None
    last_scan_status: str | None
    last_scan_message: str | None
    packages_found_last_scan: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailCredentialTestRequest(BaseModel):
    imap_server: str
    imap_port: int = 993
    email_address: EmailStr
    password: str  # Not stored, just for testing


class EmailCredentialTestResponse(BaseModel):
    success: bool
    message: str
