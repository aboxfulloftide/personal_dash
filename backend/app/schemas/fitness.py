from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class WeightEntryCreate(BaseModel):
    weight: float
    unit: str = "lbs"
    notes: Optional[str] = None
    recorded_at: date


class WeightEntryResponse(BaseModel):
    id: int
    user_id: int
    weight: float
    unit: str
    notes: Optional[str]
    recorded_at: date
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class GarminConnectRequest(BaseModel):
    email: str
    password: str


class GarminStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    sync_enabled: bool = False
    last_synced_at: Optional[datetime] = None
    sync_status: str = "never"
    sync_error: Optional[str] = None


class GarminDailyStatResponse(BaseModel):
    date: date
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    sleep_minutes: Optional[int] = None
    resting_hr: Optional[int] = None

    class Config:
        from_attributes = True


class GarminActivityResponse(BaseModel):
    id: int
    garmin_activity_id: str
    activity_type: Optional[str] = None
    name: Optional[str] = None
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    calories: Optional[int] = None
    avg_hr: Optional[int] = None

    class Config:
        from_attributes = True


class FitnessStatsResponse(BaseModel):
    # Today's Garmin stats (may be None if not connected or no data)
    today_steps: Optional[int] = None
    today_active_calories: Optional[int] = None
    today_sleep_minutes: Optional[int] = None
    today_resting_hr: Optional[int] = None

    # Latest weight (from manual or Garmin)
    latest_weight: Optional[float] = None
    latest_weight_unit: str = "lbs"
    latest_weight_date: Optional[date] = None

    # Weight history for chart
    weight_history: list[WeightEntryResponse] = []

    # Recent activities
    recent_activities: list[GarminActivityResponse] = []

    # Garmin connection status
    garmin_connected: bool = False
    garmin_sync_status: str = "never"
    garmin_last_synced_at: Optional[datetime] = None
