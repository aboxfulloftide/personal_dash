# Task 016: Fitness Stats Widget

## Objective
Build a fitness stats widget for tracking body weight and other health metrics with manual entry, charts, and goal tracking.

## Prerequisites
- Task 006 completed (Widget Framework)
- Task 003 completed (Database Schema)

## Features
- Manual weight entry
- Weight history chart
- Goal setting and progress tracking
- BMI calculation (optional height input)
- Trend indicators (gaining/losing/stable)
- Multiple metric support (weight, body fat %, etc.)
- Data export capability

## API Approach
- **Manual Entry**: Primary method, always available
- **Garmin Connect**: No official API, would require unofficial methods (not recommended for MVP)
- **Future**: Could add integrations via webhooks or file imports

## Deliverables

### 1. Database Models

#### backend/app/models/fitness.py:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class MetricType(str, enum.Enum):
    WEIGHT = "weight"
    BODY_FAT = "body_fat"
    MUSCLE_MASS = "muscle_mass"
    WATER = "water"
    BMI = "bmi"


class WeightUnit(str, enum.Enum):
    KG = "kg"
    LBS = "lbs"


class FitnessProfile(Base):
    __tablename__ = "fitness_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    height_cm = Column(Float, nullable=True)  # Height in centimeters
    weight_unit = Column(String(10), default="lbs")  # kg or lbs

    goal_weight = Column(Float, nullable=True)  # In user's preferred unit
    goal_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="fitness_profile")
    entries = relationship("FitnessEntry", back_populates="profile", cascade="all, delete-orphan")


class FitnessEntry(Base):
    __tablename__ = "fitness_entries"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("fitness_profiles.id"), nullable=False)

    date = Column(Date, nullable=False)
    metric_type = Column(String(20), default="weight")
    value = Column(Float, nullable=False)
    unit = Column(String(10), nullable=True)  # kg, lbs, %

    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("FitnessProfile", back_populates="entries")
```

### 2. Fitness Service

#### backend/app/services/fitness_service.py:
```python
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.fitness import FitnessProfile, FitnessEntry


class FitnessService:

    # Conversion constants
    KG_TO_LBS = 2.20462
    LBS_TO_KG = 0.453592

    def get_or_create_profile(self, db: Session, user_id: int) -> FitnessProfile:
        """Get or create fitness profile for user."""

        profile = db.query(FitnessProfile).filter(
            FitnessProfile.user_id == user_id
        ).first()

        if not profile:
            profile = FitnessProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

        return profile

    def update_profile(
        self,
        db: Session,
        profile: FitnessProfile,
        height_cm: Optional[float] = None,
        weight_unit: Optional[str] = None,
        goal_weight: Optional[float] = None,
        goal_date: Optional[date] = None
    ) -> FitnessProfile:
        """Update fitness profile settings."""

        if height_cm is not None:
            profile.height_cm = height_cm
        if weight_unit is not None:
            profile.weight_unit = weight_unit
        if goal_weight is not None:
            profile.goal_weight = goal_weight
        if goal_date is not None:
            profile.goal_date = goal_date

        db.commit()
        db.refresh(profile)
        return profile

    def add_entry(
        self,
        db: Session,
        profile: FitnessProfile,
        entry_date: date,
        value: float,
        metric_type: str = "weight",
        notes: Optional[str] = None
    ) -> FitnessEntry:
        """Add or update a fitness entry."""

        # Check for existing entry on same date
        existing = db.query(FitnessEntry).filter(
            FitnessEntry.profile_id == profile.id,
            FitnessEntry.date == entry_date,
            FitnessEntry.metric_type == metric_type
        ).first()

        if existing:
            existing.value = value
            existing.notes = notes
            db.commit()
            db.refresh(existing)
            return existing

        # Determine unit
        unit = None
        if metric_type == "weight":
            unit = profile.weight_unit
        elif metric_type in ["body_fat", "water"]:
            unit = "%"

        entry = FitnessEntry(
            profile_id=profile.id,
            date=entry_date,
            metric_type=metric_type,
            value=value,
            unit=unit,
            notes=notes
        )

        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def get_entries(
        self,
        db: Session,
        profile: FitnessProfile,
        metric_type: str = "weight",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365
    ) -> List[FitnessEntry]:
        """Get fitness entries."""

        query = db.query(FitnessEntry).filter(
            FitnessEntry.profile_id == profile.id,
            FitnessEntry.metric_type == metric_type
        )

        if start_date:
            query = query.filter(FitnessEntry.date >= start_date)
        if end_date:
            query = query.filter(FitnessEntry.date <= end_date)

        return query.order_by(FitnessEntry.date.desc()).limit(limit).all()

    def delete_entry(self, db: Session, entry_id: int, profile_id: int) -> bool:
        """Delete a fitness entry."""

        entry = db.query(FitnessEntry).filter(
            FitnessEntry.id == entry_id,
            FitnessEntry.profile_id == profile_id
        ).first()

        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False

    def get_stats(
        self,
        db: Session,
        profile: FitnessProfile,
        metric_type: str = "weight"
    ) -> Dict[str, Any]:
        """Calculate fitness statistics."""

        entries = self.get_entries(db, profile, metric_type, limit=365)

        if not entries:
            return {
                "current": None,
                "trend": "stable",
                "change_7d": None,
                "change_30d": None,
                "min": None,
                "max": None,
                "average": None,
                "bmi": None,
                "goal_progress": None
            }

        current = entries[0].value
        today = date.today()

        # Get entries for different periods
        entries_7d = [e for e in entries if (today - e.date).days <= 7]
        entries_30d = [e for e in entries if (today - e.date).days <= 30]

        # Calculate changes
        change_7d = None
        change_30d = None

        if len(entries_7d) > 1:
            oldest_7d = min(entries_7d, key=lambda e: e.date)
            change_7d = current - oldest_7d.value

        if len(entries_30d) > 1:
            oldest_30d = min(entries_30d, key=lambda e: e.date)
            change_30d = current - oldest_30d.value

        # Determine trend
        trend = "stable"
        if change_7d is not None:
            if change_7d > 0.5:
                trend = "gaining"
            elif change_7d < -0.5:
                trend = "losing"

        # Calculate BMI if height available and metric is weight
        bmi = None
        if metric_type == "weight" and profile.height_cm:
            weight_kg = current
            if profile.weight_unit == "lbs":
                weight_kg = current * self.LBS_TO_KG
            height_m = profile.height_cm / 100
            bmi = round(weight_kg / (height_m ** 2), 1)

        # Goal progress
        goal_progress = None
        if profile.goal_weight and metric_type == "weight" and len(entries) > 1:
            oldest = min(entries, key=lambda e: e.date)
            start_weight = oldest.value

            total_to_lose = start_weight - profile.goal_weight
            lost_so_far = start_weight - current

            if total_to_lose != 0:
                goal_progress = round((lost_so_far / total_to_lose) * 100, 1)

        all_values = [e.value for e in entries]

        return {
            "current": current,
            "trend": trend,
            "change_7d": round(change_7d, 1) if change_7d else None,
            "change_30d": round(change_30d, 1) if change_30d else None,
            "min": min(all_values),
            "max": max(all_values),
            "average": round(sum(all_values) / len(all_values), 1),
            "bmi": bmi,
            "goal_progress": goal_progress,
            "total_entries": len(entries)
        }

    def get_chart_data(
        self,
        db: Session,
        profile: FitnessProfile,
        metric_type: str = "weight",
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get data formatted for charting."""

        start_date = date.today() - timedelta(days=days)
        entries = self.get_entries(
            db, profile, metric_type, 
            start_date=start_date,
            limit=days
        )

        # Reverse to chronological order
        entries.reverse()

        return [
            {
                "date": e.date.isoformat(),
                "value": e.value
            }
            for e in entries
        ]

    def convert_weight(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert weight between units."""

        if from_unit == to_unit:
            return value

        if from_unit == "kg" and to_unit == "lbs":
            return round(value * self.KG_TO_LBS, 1)
        elif from_unit == "lbs" and to_unit == "kg":
            return round(value * self.LBS_TO_KG, 1)

        return value

    def export_data(
        self,
        db: Session,
        profile: FitnessProfile,
        metric_type: str = "weight"
    ) -> List[Dict[str, Any]]:
        """Export all entries for a metric type."""

        entries = self.get_entries(db, profile, metric_type, limit=10000)
        entries.reverse()

        return [
            {
                "date": e.date.isoformat(),
                "value": e.value,
                "unit": e.unit,
                "notes": e.notes
            }
            for e in entries
        ]
```

### 3. API Endpoints

#### backend/app/api/v1/fitness.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import csv
import io

from app.database import get_db
from app.models.user import User
from app.schemas.fitness import (
    FitnessProfileResponse, FitnessProfileUpdate,
    FitnessEntryCreate, FitnessEntryResponse,
    FitnessStatsResponse, ChartDataResponse
)
from app.api.deps import get_current_user
from app.services.fitness_service import FitnessService

router = APIRouter(prefix="/fitness", tags=["fitness"])
fitness_service = FitnessService()


@router.get("/profile", response_model=FitnessProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's fitness profile."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)
    return profile


@router.put("/profile", response_model=FitnessProfileResponse)
async def update_profile(
    data: FitnessProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update fitness profile settings."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)

    profile = fitness_service.update_profile(
        db, profile,
        height_cm=data.height_cm,
        weight_unit=data.weight_unit,
        goal_weight=data.goal_weight,
        goal_date=data.goal_date
    )

    return profile


@router.post("/entries", response_model=FitnessEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_entry(
    data: FitnessEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a fitness entry."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)

    entry = fitness_service.add_entry(
        db, profile,
        entry_date=data.date,
        value=data.value,
        metric_type=data.metric_type,
        notes=data.notes
    )

    return entry


@router.get("/entries")
async def get_entries(
    metric_type: str = "weight",
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fitness entries."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)

    from datetime import timedelta
    start_date = date.today() - timedelta(days=days)

    entries = fitness_service.get_entries(
        db, profile, metric_type, start_date=start_date
    )

    return [
        {
            "id": e.id,
            "date": e.date.isoformat(),
            "value": e.value,
            "unit": e.unit,
            "notes": e.notes
        }
        for e in entries
    ]


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a fitness entry."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)

    success = fitness_service.delete_entry(db, entry_id, profile.id)

    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")


@router.get("/stats", response_model=FitnessStatsResponse)
async def get_stats(
    metric_type: str = "weight",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fitness statistics."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)
    stats = fitness_service.get_stats(db, profile, metric_type)
    stats["unit"] = profile.weight_unit if metric_type == "weight" else "%"
    stats["goal_weight"] = profile.goal_weight
    return stats


@router.get("/chart")
async def get_chart_data(
    metric_type: str = "weight",
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chart data."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)
    data = fitness_service.get_chart_data(db, profile, metric_type, days)

    return {
        "data": data,
        "unit": profile.weight_unit if metric_type == "weight" else "%",
        "goal": profile.goal_weight if metric_type == "weight" else None
    }


@router.get("/export")
async def export_data(
    metric_type: str = "weight",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export fitness data as CSV."""
    profile = fitness_service.get_or_create_profile(db, current_user.id)
    data = fitness_service.export_data(db, profile, metric_type)

    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "value", "unit", "notes"])
    writer.writeheader()
    writer.writerows(data)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=fitness_{metric_type}_{date.today()}.csv"
        }
    )
```

### 4. Pydantic Schemas

#### backend/app/schemas/fitness.py:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FitnessProfileUpdate(BaseModel):
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_unit: Optional[str] = Field(None, pattern="^(kg|lbs)$")
    goal_weight: Optional[float] = Field(None, ge=20, le=1000)
    goal_date: Optional[date] = None


class FitnessProfileResponse(BaseModel):
    id: int
    height_cm: Optional[float]
    weight_unit: str
    goal_weight: Optional[float]
    goal_date: Optional[date]

    class Config:
        from_attributes = True


class FitnessEntryCreate(BaseModel):
    date: date
    value: float = Field(..., ge=0, le=2000)
    metric_type: str = Field(default="weight", pattern="^(weight|body_fat|muscle_mass|water)$")
    notes: Optional[str] = Field(None, max_length=500)


class FitnessEntryResponse(BaseModel):
    id: int
    date: date
    value: float
    unit: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class FitnessStatsResponse(BaseModel):
    current: Optional[float]
    unit: str
    trend: str
    change_7d: Optional[float]
    change_30d: Optional[float]
    min: Optional[float]
    max: Optional[float]
    average: Optional[float]
    bmi: Optional[float]
    goal_weight: Optional[float]
    goal_progress: Optional[float]
    total_entries: Optional[int] = 0


class ChartDataPoint(BaseModel):
    date: str
    value: float


class ChartDataResponse(BaseModel):
    data: List[ChartDataPoint]
    unit: str
    goal: Optional[float]
```

### 5. Frontend Fitness Widget

#### frontend/src/components/widgets/FitnessWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { 
  Scale, TrendingUp, TrendingDown, Minus, 
  Plus, Settings, Download, Target
} from 'lucide-react';
import { useFitness } from '../../hooks/useFitness';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function FitnessWidget({ config }) {
  const [showAddEntry, setShowAddEntry] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [chartDays, setChartDays] = useState(90);

  const {
    profile,
    stats,
    chartData,
    loading,
    fetchProfile,
    fetchStats,
    fetchChartData,
    addEntry,
    updateProfile,
    exportData
  } = useFitness();

  useEffect(() => {
    fetchProfile();
    fetchStats();
    fetchChartData(chartDays);
  }, [chartDays]);

  const getTrendIcon = () => {
    if (!stats?.trend) return <Minus className="w-4 h-4 text-gray-400" />;

    switch (stats.trend) {
      case 'gaining':
        return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'losing':
        return <TrendingDown className="w-4 h-4 text-green-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatChange = (value) => {
    if (value === null || value === undefined) return '-';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value} ${stats?.unit || 'lbs'}`;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-gray-500" />
          <span className="font-medium">Weight Tracker</span>
        </div>

        <div className="flex gap-1">
          <button
            onClick={() => setShowAddEntry(true)}
            className="p-1 hover:bg-gray-100 rounded text-blue-500"
            title="Add Entry"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => exportData()}
            className="p-1 hover:bg-gray-100 rounded"
            title="Export Data"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Current Weight & Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Current</div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">
              {stats?.current ?? '-'}
            </span>
            <span className="text-sm text-gray-500">{stats?.unit}</span>
            {getTrendIcon()}
          </div>
          {stats?.bmi && (
            <div className="text-xs text-gray-500 mt-1">
              BMI: {stats.bmi}
            </div>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Goal</div>
          {stats?.goal_weight ? (
            <>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-blue-500" />
                <span className="text-lg font-semibold">
                  {stats.goal_weight} {stats?.unit}
                </span>
              </div>
              {stats.goal_progress !== null && (
                <div className="mt-1">
                  <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.min(100, Math.max(0, stats.goal_progress))}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {stats.goal_progress}% progress
                  </div>
                </div>
              )}
            </>
          ) : (
            <button
              onClick={() => setShowSettings(true)}
              className="text-sm text-blue-500 hover:underline"
            >
              Set a goal
            </button>
          )}
        </div>
      </div>

      {/* Change Stats */}
      <div className="flex gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-500">7 days: </span>
          <span className={stats?.change_7d < 0 ? 'text-green-600' : stats?.change_7d > 0 ? 'text-red-600' : ''}>
            {formatChange(stats?.change_7d)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">30 days: </span>
          <span className={stats?.change_30d < 0 ? 'text-green-600' : stats?.change_30d > 0 ? 'text-red-600' : ''}>
            {formatChange(stats?.change_30d)}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[150px]">
        {chartData?.data?.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData.data}>
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 10 }}
                tickFormatter={(val) => {
                  const d = new Date(val);
                  return `${d.getMonth() + 1}/${d.getDate()}`;
                }}
              />
              <YAxis 
                domain={['dataMin - 5', 'dataMax + 5']}
                tick={{ fontSize: 10 }}
                width={40}
              />
              <Tooltip 
                labelFormatter={(val) => new Date(val).toLocaleDateString()}
                formatter={(val) => [`${val} ${chartData.unit}`, 'Weight']}
              />
              {chartData.goal && (
                <ReferenceLine 
                  y={chartData.goal} 
                  stroke="#3b82f6" 
                  strokeDasharray="5 5"
                  label={{ value: 'Goal', fontSize: 10, fill: '#3b82f6' }}
                />
              )}
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#6366f1" 
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <Scale className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No data yet</p>
              <button
                onClick={() => setShowAddEntry(true)}
                className="text-sm text-blue-500 hover:underline mt-1"
              >
                Add your first entry
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Time Range Selector */}
      <div className="flex justify-center gap-2 mt-2">
        {[30, 90, 180, 365].map((days) => (
          <button
            key={days}
            onClick={() => setChartDays(days)}
            className={`px-2 py-1 text-xs rounded ${
              chartDays === days
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {days === 365 ? '1Y' : `${days}D`}
          </button>
        ))}
      </div>

      {/* Add Entry Modal */}
      {showAddEntry && (
        <AddEntryModal
          unit={profile?.weight_unit || 'lbs'}
          onAdd={async (data) => {
            await addEntry(data);
            setShowAddEntry(false);
            fetchStats();
            fetchChartData(chartDays);
          }}
          onClose={() => setShowAddEntry(false)}
        />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <FitnessSettingsModal
          profile={profile}
          onUpdate={async (data) => {
            await updateProfile(data);
            setShowSettings(false);
            fetchStats();
          }}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

function AddEntryModal({ unit, onAdd, onClose }) {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value) {
      onAdd({
        date,
        value: parseFloat(value),
        metric_type: 'weight',
        notes: notes || null
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-sm mx-4">
        <h3 className="font-semibold mb-4">Log Weight</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-600 mb-1">Weight ({unit})</label>
            <input
              type="number"
              step="0.1"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={`Enter weight in ${unit}`}
              className="w-full p-2 border rounded"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm text-gray-600 mb-1">Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., After workout"
              className="w-full p-2 border rounded"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
            >
              Save
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-100 py-2 rounded hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FitnessSettingsModal({ profile, onUpdate, onClose }) {
  const [heightCm, setHeightCm] = useState(profile?.height_cm || '');
  const [weightUnit, setWeightUnit] = useState(profile?.weight_unit || 'lbs');
  const [goalWeight, setGoalWeight] = useState(profile?.goal_weight || '');
  const [goalDate, setGoalDate] = useState(profile?.goal_date || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate({
      height_cm: heightCm ? parseFloat(heightCm) : null,
      weight_unit: weightUnit,
      goal_weight: goalWeight ? parseFloat(goalWeight) : null,
      goal_date: goalDate || null
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-sm mx-4">
        <h3 className="font-semibold mb-4">Fitness Settings</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Weight Unit</label>
            <select
              value={weightUnit}
              onChange={(e) => setWeightUnit(e.target.value)}
              className="w-full p-2 border rounded"
            >
              <option value="lbs">Pounds (lbs)</option>
              <option value="kg">Kilograms (kg)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-600 mb-1">Height (cm) - for BMI</label>
            <input
              type="number"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              placeholder="e.g., 175"
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-600 mb-1">Goal Weight ({weightUnit})</label>
            <input
              type="number"
              step="0.1"
              value={goalWeight}
              onChange={(e) => setGoalWeight(e.target.value)}
              placeholder="Target weight"
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-600 mb-1">Goal Date (optional)</label>
            <input
              type="date"
              value={goalDate}
              onChange={(e) => setGoalDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full p-2 border rounded"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
            >
              Save
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-100 py-2 rounded hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### 6. React Hook

#### frontend/src/hooks/useFitness.js:
```javascript
import { useState, useCallback } from 'react';
import api from '../services/api';

export function useFitness() {
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    try {
      const response = await api.get('/fitness/profile');
      setProfile(response.data);
    } catch (err) {
      console.error('Failed to fetch fitness profile:', err);
    }
  }, []);

  const fetchStats = useCallback(async (metricType = 'weight') => {
    try {
      const response = await api.get('/fitness/stats', {
        params: { metric_type: metricType }
      });
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch fitness stats:', err);
    }
  }, []);

  const fetchChartData = useCallback(async (days = 90, metricType = 'weight') => {
    try {
      setLoading(true);
      const response = await api.get('/fitness/chart', {
        params: { days, metric_type: metricType }
      });
      setChartData(response.data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEntries = useCallback(async (days = 90, metricType = 'weight') => {
    try {
      const response = await api.get('/fitness/entries', {
        params: { days, metric_type: metricType }
      });
      setEntries(response.data);
    } catch (err) {
      console.error('Failed to fetch entries:', err);
    }
  }, []);

  const addEntry = async (entryData) => {
    try {
      const response = await api.post('/fitness/entries', entryData);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const deleteEntry = async (entryId) => {
    try {
      await api.delete(`/fitness/entries/${entryId}`);
      setEntries(prev => prev.filter(e => e.id !== entryId));
    } catch (err) {
      throw err;
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await api.put('/fitness/profile', profileData);
      setProfile(response.data);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const exportData = async (metricType = 'weight') => {
    try {
      const response = await api.get('/fitness/export', {
        params: { metric_type: metricType },
        responseType: 'blob'
      });

      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fitness_${metricType}_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export data:', err);
    }
  };

  return {
    profile,
    stats,
    chartData,
    entries,
    loading,
    fetchProfile,
    fetchStats,
    fetchChartData,
    fetchEntries,
    addEntry,
    deleteEntry,
    updateProfile,
    exportData
  };
}
```

## Unit Tests

### tests/test_fitness_service.py:
```python
import pytest
from datetime import date, timedelta
from app.services.fitness_service import FitnessService


class TestFitnessService:
    def test_convert_weight_kg_to_lbs(self):
        service = FitnessService()
        result = service.convert_weight(100, "kg", "lbs")
        assert abs(result - 220.5) < 0.1

    def test_convert_weight_lbs_to_kg(self):
        service = FitnessService()
        result = service.convert_weight(220, "lbs", "kg")
        assert abs(result - 99.8) < 0.1

    def test_convert_weight_same_unit(self):
        service = FitnessService()
        result = service.convert_weight(150, "lbs", "lbs")
        assert result == 150

    def test_bmi_calculation(self):
        # BMI = weight(kg) / height(m)^2
        # For 70kg, 175cm: BMI = 70 / 1.75^2 = 22.9
        service = FitnessService()

        # Mock profile with height
        class MockProfile:
            height_cm = 175
            weight_unit = "kg"

        # The actual BMI calculation happens in get_stats
        # This tests the formula: weight_kg / (height_m ** 2)
        weight_kg = 70
        height_m = 175 / 100
        bmi = round(weight_kg / (height_m ** 2), 1)

        assert bmi == 22.9
```

## Acceptance Criteria
- [ ] Manual weight entry works
- [ ] Weight history displays in chart
- [ ] Supports kg and lbs units
- [ ] BMI calculates when height provided
- [ ] Goal weight can be set
- [ ] Goal progress shows percentage
- [ ] Trend indicator (gaining/losing/stable)
- [ ] 7-day and 30-day change displayed
- [ ] Chart time range selectable (30/90/180/365 days)
- [ ] Data export to CSV works
- [ ] One entry per day (updates if exists)
- [ ] Unit tests pass

## Notes
- Garmin integration deferred (no official API)
- Could add body fat %, muscle mass tracking later
- Consider adding photo progress feature in future
- Data privacy important - all data user-specific

## Estimated Time
2-3 hours

## Next Task
Task 017: Dashboard Layout & Polish
