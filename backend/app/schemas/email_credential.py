from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class EmailCredentialBase(BaseModel):
    imap_server: str
    imap_port: int = 993
    email_address: EmailStr
    enabled: bool = True
    scan_interval_hours: int = 1
    days_to_scan: int = 30

    @field_validator('imap_server')
    @classmethod
    def trim_imap_server(cls, v: str) -> str:
        return v.strip() if v else v


class EmailCredentialCreate(EmailCredentialBase):
    password: str  # Plain password, will be encrypted before storage

    @field_validator('password')
    @classmethod
    def trim_password(cls, v: str) -> str:
        return v.strip() if v else v


class EmailCredentialUpdate(BaseModel):
    imap_server: str | None = None
    imap_port: int | None = None
    email_address: EmailStr | None = None
    password: str | None = None  # Plain password, will be encrypted before storage
    enabled: bool | None = None
    scan_interval_hours: int | None = None
    days_to_scan: int | None = None

    @field_validator('imap_server', 'password')
    @classmethod
    def trim_strings(cls, v: str | None) -> str | None:
        return v.strip() if v else v


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

    @field_validator('imap_server', 'password')
    @classmethod
    def trim_strings(cls, v: str) -> str:
        return v.strip() if v else v


class EmailCredentialTestResponse(BaseModel):
    success: bool
    message: str
