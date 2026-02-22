from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    widget_configs = relationship("WidgetConfig", back_populates="user", cascade="all, delete-orphan")
    dashboard_layouts = relationship("DashboardLayout", back_populates="user", cascade="all, delete-orphan")
    servers = relationship("Server", back_populates="user", cascade="all, delete-orphan")
    packages = relationship("Package", back_populates="user", cascade="all, delete-orphan")
    weight_entries = relationship("WeightEntry", back_populates="user", cascade="all, delete-orphan")
    email_accounts = relationship("EmailAccount", back_populates="user", cascade="all, delete-orphan")
    email_credential = relationship("EmailCredential", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    reminder_instances = relationship("ReminderInstance", back_populates="user", cascade="all, delete-orphan")
    garmin_credential = relationship("GarminCredential", back_populates="user", uselist=False, cascade="all, delete-orphan")
    garmin_daily_stats = relationship("GarminDailyStat", back_populates="user", cascade="all, delete-orphan")
    garmin_activities = relationship("GarminActivity", back_populates="user", cascade="all, delete-orphan")
