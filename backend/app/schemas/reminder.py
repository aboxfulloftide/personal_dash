"""Pydantic schemas for reminders."""
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReminderBase(BaseModel):
    """Base schema for reminder configuration."""
    title: str = Field(..., max_length=255, description="Reminder title")
    notes: Optional[str] = Field(None, description="Additional notes")
    recurrence_type: str = Field(..., description="Type of recurrence: 'interval' or 'day_of_week'")

    # Interval-based fields
    interval_value: Optional[int] = Field(None, gt=0, description="Interval value (e.g., 4 for every 4 hours)")
    interval_unit: Optional[str] = Field(None, description="Interval unit: 'hours', 'days', 'weeks', 'months'")

    # Day-of-week based fields
    days_of_week: Optional[str] = Field(None, description="Comma-separated day numbers (0=Monday, 6=Sunday)")

    # Time fields
    reminder_time: Optional[time] = Field(None, description="Time for the reminder (required for day_of_week)")

    # Start date
    start_date: date = Field(..., description="Date to start the reminders")

    # Behavior
    carry_over: bool = Field(True, description="If True, missed reminders show next day; if False, auto-dismiss")
    is_active: bool = Field(True, description="Whether the reminder is active")


class ReminderCreate(ReminderBase):
    """Schema for creating a new reminder."""
    pass


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder (all fields optional)."""
    title: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    recurrence_type: Optional[str] = None
    interval_value: Optional[int] = Field(None, gt=0)
    interval_unit: Optional[str] = None
    days_of_week: Optional[str] = None
    reminder_time: Optional[time] = None
    start_date: Optional[date] = None
    carry_over: Optional[bool] = None
    is_active: Optional[bool] = None


class ReminderInDB(ReminderBase):
    """Schema for reminder as stored in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReminderResponse(ReminderInDB):
    """Schema for reminder API response."""
    pass


# ===== Reminder Instance Schemas =====


class ReminderInstanceBase(BaseModel):
    """Base schema for reminder instance."""
    due_date: date
    due_time: Optional[time] = None
    instance_number: Optional[int] = None
    status: str = Field(default="pending", description="Status: 'pending', 'dismissed', 'missed'")
    is_overdue: bool = Field(default=False, description="Is this a carried-over reminder?")


class ReminderInstanceCreate(ReminderInstanceBase):
    """Schema for creating a reminder instance."""
    reminder_id: int


class ReminderInstanceInDB(ReminderInstanceBase):
    """Schema for reminder instance as stored in database."""
    id: int
    reminder_id: int
    user_id: int
    dismissed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderInstanceResponse(ReminderInstanceInDB):
    """Schema for reminder instance API response."""
    reminder_title: Optional[str] = None  # Joined from Reminder table
    reminder_notes: Optional[str] = None  # Joined from Reminder table


class ReminderInstanceUpdate(BaseModel):
    """Schema for updating a reminder instance."""
    status: Optional[str] = Field(None, description="Status: 'pending', 'dismissed', 'missed'")


# ===== Combined Schemas for Dashboard Display =====


class TodayReminderDisplay(BaseModel):
    """Combined schema for displaying today's reminders in widget."""
    instance_id: int
    reminder_id: int
    title: str
    notes: Optional[str] = None
    due_date: date
    due_time: Optional[time] = None
    instance_number: Optional[int] = None  # For hourly reminders
    status: str
    is_overdue: bool
    dismissed_at: Optional[datetime] = None


class RemindersWidgetResponse(BaseModel):
    """Response schema for reminders widget data."""
    reminders: list[TodayReminderDisplay]
    total_count: int
    pending_count: int
    overdue_count: int
