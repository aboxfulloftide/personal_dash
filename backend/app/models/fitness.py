from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    unit = Column(String(10), default="lbs")
    notes = Column(Text)
    recorded_at = Column(Date, nullable=False)
    source = Column(String(20), default="manual")  # 'manual' or 'garmin'
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="weight_entries")


class GarminCredential(Base):
    __tablename__ = "garmin_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    garmin_username = Column(String(255), nullable=True)  # Garmin display name for API calls
    encrypted_tokens = Column(Text, nullable=True)  # JSON of serialized garth OAuth tokens
    sync_enabled = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="never")  # 'ok', 'error', 'never'
    sync_error = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="garmin_credential")


class GarminDailyStat(Base):
    __tablename__ = "garmin_daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    steps = Column(Integer, nullable=True)
    active_calories = Column(Integer, nullable=True)
    sleep_minutes = Column(Integer, nullable=True)
    resting_hr = Column(Integer, nullable=True)
    synced_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="garmin_daily_stats")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_garmin_daily_user_date'),
        Index('idx_garmin_daily_user_date', 'user_id', 'date'),
    )


class GarminActivity(Base):
    __tablename__ = "garmin_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    garmin_activity_id = Column(String(100), nullable=False)
    activity_type = Column(String(100), nullable=True)
    name = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    distance_km = Column(Numeric(8, 3), nullable=True)
    calories = Column(Integer, nullable=True)
    avg_hr = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="garmin_activities")

    __table_args__ = (
        UniqueConstraint('user_id', 'garmin_activity_id', name='uq_garmin_activity_user_id'),
        Index('idx_garmin_activity_user_time', 'user_id', 'start_time'),
    )
