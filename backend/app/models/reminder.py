from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Reminder(Base):
    """Recurring reminder configuration"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    # Recurrence settings
    recurrence_type = Column(String(20), nullable=False)  # "interval", "day_of_week"

    # For interval-based reminders
    interval_value = Column(Integer, nullable=True)  # The number (e.g., 4)
    interval_unit = Column(String(20), nullable=True)  # "hours", "days", "weeks", "months"

    # For day-of-week based reminders (comma-separated: "0,1,2,3,4,5,6" where 0=Monday)
    days_of_week = Column(String(20), nullable=True)

    # Time for hourly reminders or day-of-week reminders
    reminder_time = Column(Time, nullable=True)

    # Start date for the reminder
    start_date = Column(Date, nullable=False)

    # Missed reminder behavior
    carry_over = Column(Boolean, default=True)  # True = show next day, False = auto-dismiss

    # Active status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reminders")
    instances = relationship("ReminderInstance", back_populates="reminder", cascade="all, delete-orphan")

    # Index for queries
    __table_args__ = (
        Index('idx_user_active', 'user_id', 'is_active'),
    )


class ReminderInstance(Base):
    """Individual occurrences of reminders for a specific date"""
    __tablename__ = "reminder_instances"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # When this instance is for
    due_date = Column(Date, nullable=False)
    due_time = Column(Time, nullable=True)  # For hourly reminders

    # Instance number for hourly reminders (1, 2, 3, etc.)
    instance_number = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # "pending", "dismissed", "missed"
    dismissed_at = Column(DateTime, nullable=True)

    # Is this overdue (carried over from previous day)?
    is_overdue = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="reminder_instances")
    reminder = relationship("Reminder", back_populates="instances")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_user_due_date_status', 'user_id', 'due_date', 'status'),
        Index('idx_reminder_due', 'reminder_id', 'due_date'),
    )
