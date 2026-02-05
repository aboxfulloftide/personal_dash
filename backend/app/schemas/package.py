from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Carrier(str, Enum):
    USPS = "usps"
    UPS = "ups"
    FEDEX = "fedex"
    AMAZON = "amazon"
    DHL = "dhl"
    OTHER = "other"


class PackageCreate(BaseModel):
    """Schema for creating a new package."""
    tracking_number: str = Field(..., min_length=1, max_length=100)
    carrier: Carrier
    description: Optional[str] = Field(None, max_length=255)


class PackageUpdate(BaseModel):
    """Schema for updating a package."""
    description: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=100)
    estimated_delivery: Optional[date] = None
    delivered: Optional[bool] = None


class PackageResponse(BaseModel):
    """Schema for package response."""
    id: int
    tracking_number: str
    carrier: str
    description: Optional[str]
    status: Optional[str]
    estimated_delivery: Optional[date]
    delivered: bool
    delivered_at: Optional[datetime]
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PackageEventCreate(BaseModel):
    """Schema for adding a tracking event."""
    status: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    event_time: Optional[datetime] = None


class PackageEventResponse(BaseModel):
    """Schema for package event response."""
    id: int
    status: str
    location: Optional[str]
    event_time: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class PackageDetail(BaseModel):
    """Schema for package with events."""
    package: PackageResponse
    events: list[PackageEventResponse]
