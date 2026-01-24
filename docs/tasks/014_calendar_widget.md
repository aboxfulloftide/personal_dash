# Task 014: Calendar Widget

## Objective
Build a calendar widget that displays events from connected calendar sources (Google Calendar, iCal URLs) with a clean monthly/weekly view.

## Prerequisites
- Task 006 completed (Widget Framework)
- Task 003 completed (Database Schema)

## Features
- Monthly calendar view with event indicators
- Weekly agenda view
- Multiple calendar source support
- iCal/ICS URL import (Google Calendar public URLs, etc.)
- Color-coded calendars
- Event details on click
- Today indicator
- Mini calendar navigation

## API Approach
- **iCal/ICS URLs**: Free, no API key needed
- Google Calendar can export public/shared calendars as ICS URLs
- Outlook can also provide ICS URLs
- Direct Google Calendar API integration can be added later

## Deliverables

### 1. Database Models

#### backend/app/models/calendar.py:
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class CalendarSource(Base):
    __tablename__ = "calendar_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(100), nullable=False)
    source_type = Column(String(20), nullable=False)  # "ical", "google", "manual"
    url = Column(String(500), nullable=True)  # iCal URL
    color = Column(String(7), default="#3b82f6")  # Hex color

    is_active = Column(Boolean, default=True)
    last_synced = Column(DateTime, nullable=True)
    sync_error = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="calendar_sources")
    events = relationship("CalendarEvent", back_populates="source", cascade="all, delete-orphan")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("calendar_sources.id"), nullable=False)

    uid = Column(String(255), nullable=True)  # iCal UID for deduplication
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)

    recurrence_rule = Column(String(500), nullable=True)  # RRULE string

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("CalendarSource", back_populates="events")
```

### 2. Calendar Service

#### backend/app/services/calendar_service.py:
```python
import httpx
from icalendar import Calendar as ICalendar
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from dateutil import rrule
from dateutil.parser import parse as parse_date

from sqlalchemy.orm import Session
from app.models.calendar import CalendarSource, CalendarEvent


class ICalService:
    """Service for parsing iCal/ICS feeds."""

    async def fetch_and_parse(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse an iCal URL."""

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            ical_data = response.text

        return self.parse_ical(ical_data)

    def parse_ical(self, ical_data: str) -> List[Dict[str, Any]]:
        """Parse iCal data into event dictionaries."""

        cal = ICalendar.from_ical(ical_data)
        events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event:
                    events.append(event)

        return events

    def _parse_event(self, component) -> Optional[Dict[str, Any]]:
        """Parse a single VEVENT component."""

        try:
            # Get start time
            dtstart = component.get('dtstart')
            if not dtstart:
                return None

            start = dtstart.dt
            all_day = not isinstance(start, datetime)

            if all_day:
                start = datetime.combine(start, datetime.min.time())

            # Get end time
            dtend = component.get('dtend')
            if dtend:
                end = dtend.dt
                if not isinstance(end, datetime):
                    end = datetime.combine(end, datetime.min.time())
            else:
                end = start + timedelta(hours=1)

            # Get recurrence rule
            rrule_prop = component.get('rrule')
            rrule_str = rrule_prop.to_ical().decode() if rrule_prop else None

            return {
                "uid": str(component.get('uid', '')),
                "title": str(component.get('summary', 'Untitled')),
                "description": str(component.get('description', '')) or None,
                "location": str(component.get('location', '')) or None,
                "start_time": start,
                "end_time": end,
                "all_day": all_day,
                "recurrence_rule": rrule_str
            }
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None


class CalendarService:
    """Main calendar service."""

    def __init__(self):
        self.ical_service = ICalService()

    async def sync_calendar_source(
        self, 
        db: Session, 
        source: CalendarSource
    ) -> Dict[str, Any]:
        """Sync events from a calendar source."""

        if source.source_type != "ical" or not source.url:
            return {"error": "Invalid source type or missing URL"}

        try:
            events = await self.ical_service.fetch_and_parse(source.url)

            # Clear existing events for this source
            db.query(CalendarEvent).filter(
                CalendarEvent.source_id == source.id
            ).delete()

            # Add new events
            added = 0
            for event_data in events:
                event = CalendarEvent(
                    source_id=source.id,
                    **event_data
                )
                db.add(event)
                added += 1

            # Update source
            source.last_synced = datetime.utcnow()
            source.sync_error = None

            db.commit()

            return {"success": True, "events_added": added}

        except Exception as e:
            source.sync_error = str(e)[:500]
            db.commit()
            return {"error": str(e)}

    def get_events_in_range(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        source_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get events within a date range."""

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        query = db.query(CalendarEvent).join(CalendarSource).filter(
            CalendarSource.user_id == user_id,
            CalendarSource.is_active == True,
            CalendarEvent.start_time <= end_dt,
            CalendarEvent.end_time >= start_dt
        )

        if source_ids:
            query = query.filter(CalendarSource.id.in_(source_ids))

        events = query.order_by(CalendarEvent.start_time).all()

        result = []
        for event in events:
            # Handle recurring events
            if event.recurrence_rule:
                recurring = self._expand_recurring_event(event, start_dt, end_dt)
                result.extend(recurring)
            else:
                result.append(self._event_to_dict(event))

        # Sort by start time
        result.sort(key=lambda x: x["start_time"])

        return result

    def _expand_recurring_event(
        self, 
        event: CalendarEvent, 
        start_dt: datetime, 
        end_dt: datetime
    ) -> List[Dict[str, Any]]:
        """Expand a recurring event into individual occurrences."""

        try:
            rule = rrule.rrulestr(
                f"RRULE:{event.recurrence_rule}",
                dtstart=event.start_time
            )

            duration = (event.end_time - event.start_time) if event.end_time else timedelta(hours=1)

            occurrences = []
            for dt in rule.between(start_dt, end_dt, inc=True):
                occurrence = self._event_to_dict(event)
                occurrence["start_time"] = dt.isoformat()
                occurrence["end_time"] = (dt + duration).isoformat()
                occurrence["is_recurring"] = True
                occurrences.append(occurrence)

            return occurrences[:50]  # Limit to 50 occurrences

        except Exception as e:
            print(f"Error expanding recurring event: {e}")
            return [self._event_to_dict(event)]

    def _event_to_dict(self, event: CalendarEvent) -> Dict[str, Any]:
        """Convert event model to dictionary."""
        return {
            "id": event.id,
            "source_id": event.source_id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "all_day": event.all_day,
            "is_recurring": bool(event.recurrence_rule),
            "color": event.source.color if event.source else "#3b82f6"
        }

    def get_events_for_month(
        self,
        db: Session,
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, List[Dict]]:
        """Get events grouped by date for a month."""

        # Get first and last day of month (with padding for calendar view)
        first_day = date(year, month, 1)

        # Get last day of month
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # Extend range to include visible days from adjacent months
        start_date = first_day - timedelta(days=first_day.weekday())
        end_date = last_day + timedelta(days=(6 - last_day.weekday()))

        events = self.get_events_in_range(db, user_id, start_date, end_date)

        # Group by date
        events_by_date = {}
        for event in events:
            event_date = event["start_time"][:10]  # YYYY-MM-DD
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        return events_by_date
```

### 3. API Endpoints

#### backend/app/api/v1/calendar.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database import get_db
from app.models.user import User
from app.models.calendar import CalendarSource, CalendarEvent
from app.schemas.calendar import (
    CalendarSourceCreate, CalendarSourceUpdate, CalendarSourceResponse,
    CalendarEventResponse, MonthEventsResponse
)
from app.api.deps import get_current_user
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])
calendar_service = CalendarService()


# ============ Calendar Sources ============

@router.get("/sources", response_model=List[CalendarSourceResponse])
async def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's calendar sources."""
    sources = db.query(CalendarSource).filter(
        CalendarSource.user_id == current_user.id
    ).all()
    return sources


@router.post("/sources", response_model=CalendarSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_source(
    source_data: CalendarSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new calendar source."""

    # Check limit
    count = db.query(CalendarSource).filter(
        CalendarSource.user_id == current_user.id
    ).count()

    if count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 calendar sources allowed"
        )

    source = CalendarSource(
        user_id=current_user.id,
        name=source_data.name,
        source_type=source_data.source_type,
        url=source_data.url,
        color=source_data.color or "#3b82f6"
    )

    db.add(source)
    db.commit()
    db.refresh(source)

    # Initial sync if iCal
    if source.source_type == "ical" and source.url:
        await calendar_service.sync_calendar_source(db, source)
        db.refresh(source)

    return source


@router.put("/sources/{source_id}", response_model=CalendarSourceResponse)
async def update_source(
    source_id: int,
    source_data: CalendarSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a calendar source."""

    source = db.query(CalendarSource).filter(
        CalendarSource.id == source_id,
        CalendarSource.user_id == current_user.id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source_data.name is not None:
        source.name = source_data.name
    if source_data.color is not None:
        source.color = source_data.color
    if source_data.is_active is not None:
        source.is_active = source_data.is_active

    db.commit()
    db.refresh(source)

    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a calendar source."""

    source = db.query(CalendarSource).filter(
        CalendarSource.id == source_id,
        CalendarSource.user_id == current_user.id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()


@router.post("/sources/{source_id}/sync")
async def sync_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually sync a calendar source."""

    source = db.query(CalendarSource).filter(
        CalendarSource.id == source_id,
        CalendarSource.user_id == current_user.id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await calendar_service.sync_calendar_source(db, source)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ============ Events ============

@router.get("/events")
async def get_events(
    start_date: date,
    end_date: date,
    source_ids: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get events in a date range."""

    source_id_list = None
    if source_ids:
        source_id_list = [int(x) for x in source_ids.split(",")]

    events = calendar_service.get_events_in_range(
        db, current_user.id, start_date, end_date, source_id_list
    )

    return events


@router.get("/events/month/{year}/{month}")
async def get_month_events(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get events for a specific month, grouped by date."""

    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Invalid month")

    events_by_date = calendar_service.get_events_for_month(
        db, current_user.id, year, month
    )

    return {
        "year": year,
        "month": month,
        "events": events_by_date
    }


@router.get("/events/today")
async def get_today_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's events."""

    today = date.today()
    events = calendar_service.get_events_in_range(
        db, current_user.id, today, today
    )

    return events
```

### 4. Pydantic Schemas

#### backend/app/schemas/calendar.py:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime


class CalendarSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., pattern="^(ical|manual)$")
    url: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class CalendarSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None


class CalendarSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    url: Optional[str]
    color: str
    is_active: bool
    last_synced: Optional[datetime]
    sync_error: Optional[str]

    class Config:
        from_attributes = True


class CalendarEventResponse(BaseModel):
    id: int
    source_id: int
    title: str
    description: Optional[str]
    location: Optional[str]
    start_time: str
    end_time: Optional[str]
    all_day: bool
    is_recurring: bool = False
    color: str


class MonthEventsResponse(BaseModel):
    year: int
    month: int
    events: Dict[str, List[CalendarEventResponse]]
```

### 5. Frontend Calendar Widget

#### frontend/src/components/widgets/CalendarWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, ChevronRight, RefreshCw, Plus, 
  Settings, Calendar as CalendarIcon, List
} from 'lucide-react';
import { useCalendar } from '../../hooks/useCalendar';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export default function CalendarWidget({ config }) {
  const [viewMode, setViewMode] = useState('month'); // 'month' or 'agenda'
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  const { 
    events, 
    sources, 
    loading, 
    fetchMonthEvents,
    addSource,
    syncSource
  } = useCalendar();

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  useEffect(() => {
    fetchMonthEvents(year, month + 1);
  }, [year, month, fetchMonthEvents]);

  const navigateMonth = (delta) => {
    const newDate = new Date(year, month + delta, 1);
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date().toISOString().split('T')[0]);
  };

  const getDaysInMonth = () => {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();

    const days = [];

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startingDay - 1; i >= 0; i--) {
      days.push({
        date: new Date(year, month - 1, prevMonthLastDay - i),
        isCurrentMonth: false
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        date: new Date(year, month, i),
        isCurrentMonth: true
      });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false
      });
    }

    return days;
  };

  const getEventsForDate = (dateStr) => {
    return events[dateStr] || [];
  };

  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const formatDateKey = (date) => {
    return date.toISOString().split('T')[0];
  };

  const days = getDaysInMonth();

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigateMonth(-1)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-medium min-w-[140px] text-center">
            {MONTHS[month]} {year}
          </span>
          <button
            onClick={() => navigateMonth(1)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="flex gap-1">
          <button
            onClick={goToToday}
            className="text-xs px-2 py-1 hover:bg-gray-100 rounded"
          >
            Today
          </button>
          <button
            onClick={() => setViewMode(viewMode === 'month' ? 'agenda' : 'month')}
            className="p-1 hover:bg-gray-100 rounded"
            title={viewMode === 'month' ? 'Agenda View' : 'Month View'}
          >
            {viewMode === 'month' ? <List className="w-4 h-4" /> : <CalendarIcon className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {viewMode === 'month' ? (
        <>
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {DAYS.map(day => (
              <div key={day} className="text-center text-xs text-gray-500 py-1">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1 flex-1">
            {days.map((day, idx) => {
              const dateKey = formatDateKey(day.date);
              const dayEvents = getEventsForDate(dateKey);
              const isSelected = selectedDate === dateKey;

              return (
                <div
                  key={idx}
                  onClick={() => setSelectedDate(dateKey)}
                  className={`
                    min-h-[40px] p-1 rounded cursor-pointer text-xs
                    ${day.isCurrentMonth ? 'bg-white' : 'bg-gray-50 text-gray-400'}
                    ${isToday(day.date) ? 'ring-2 ring-blue-500' : ''}
                    ${isSelected ? 'bg-blue-50' : 'hover:bg-gray-100'}
                  `}
                >
                  <div className={`
                    w-5 h-5 flex items-center justify-center rounded-full mb-0.5
                    ${isToday(day.date) ? 'bg-blue-500 text-white' : ''}
                  `}>
                    {day.date.getDate()}
                  </div>

                  {/* Event Indicators */}
                  <div className="space-y-0.5">
                    {dayEvents.slice(0, 2).map((event, i) => (
                      <div
                        key={i}
                        className="truncate text-[10px] px-1 rounded"
                        style={{ backgroundColor: event.color + '30', color: event.color }}
                      >
                        {event.title}
                      </div>
                    ))}
                    {dayEvents.length > 2 && (
                      <div className="text-[10px] text-gray-500 px-1">
                        +{dayEvents.length - 2} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <AgendaView 
          events={events} 
          currentDate={currentDate}
        />
      )}

      {/* Selected Date Events */}
      {selectedDate && viewMode === 'month' && (
        <SelectedDateEvents
          date={selectedDate}
          events={getEventsForDate(selectedDate)}
          onClose={() => setSelectedDate(null)}
        />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <CalendarSettingsModal
          sources={sources}
          onAddSource={addSource}
          onSyncSource={syncSource}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

function AgendaView({ events, currentDate }) {
  // Get next 14 days of events
  const upcomingEvents = [];
  const today = new Date();

  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const dateKey = date.toISOString().split('T')[0];
    const dayEvents = events[dateKey] || [];

    if (dayEvents.length > 0) {
      upcomingEvents.push({
        date: dateKey,
        displayDate: date.toLocaleDateString('en-US', { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric' 
        }),
        events: dayEvents
      });
    }
  }

  if (upcomingEvents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        No upcoming events in the next 2 weeks
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto space-y-3">
      {upcomingEvents.map((day) => (
        <div key={day.date}>
          <div className="text-xs font-medium text-gray-500 mb-1">
            {day.displayDate}
          </div>
          <div className="space-y-1">
            {day.events.map((event, idx) => (
              <div
                key={idx}
                className="p-2 rounded-lg border-l-4"
                style={{ borderColor: event.color, backgroundColor: event.color + '10' }}
              >
                <div className="font-medium text-sm">{event.title}</div>
                {!event.all_day && (
                  <div className="text-xs text-gray-500">
                    {new Date(event.start_time).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit'
                    })}
                    {event.end_time && (
                      <> - {new Date(event.end_time).toLocaleTimeString('en-US', {
                        hour: 'numeric',
                        minute: '2-digit'
                      })}</>
                    )}
                  </div>
                )}
                {event.location && (
                  <div className="text-xs text-gray-500 mt-1">
                    📍 {event.location}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SelectedDateEvents({ date, events, onClose }) {
  const displayDate = new Date(date + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="mt-3 pt-3 border-t">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">{displayDate}</span>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ✕
        </button>
      </div>

      {events.length === 0 ? (
        <p className="text-sm text-gray-500">No events</p>
      ) : (
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {events.map((event, idx) => (
            <div
              key={idx}
              className="p-2 rounded text-sm"
              style={{ backgroundColor: event.color + '20' }}
            >
              <div className="font-medium">{event.title}</div>
              {!event.all_day && (
                <div className="text-xs text-gray-600">
                  {new Date(event.start_time).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit'
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CalendarSettingsModal({ sources, onAddSource, onSyncSource, onClose }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSource, setNewSource] = useState({ name: '', url: '', color: '#3b82f6' });

  const handleAdd = async () => {
    if (newSource.name && newSource.url) {
      await onAddSource({
        name: newSource.name,
        source_type: 'ical',
        url: newSource.url,
        color: newSource.color
      });
      setNewSource({ name: '', url: '', color: '#3b82f6' });
      setShowAddForm(false);
    }
  };

  const colorOptions = [
    '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', 
    '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Calendar Settings</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        {/* Calendar Sources */}
        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2">Calendar Sources</h4>

          {sources.length === 0 ? (
            <p className="text-sm text-gray-500 mb-2">No calendars added yet</p>
          ) : (
            <div className="space-y-2 mb-2">
              {sources.map((source) => (
                <div key={source.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: source.color }}
                    />
                    <span className="text-sm">{source.name}</span>
                  </div>
                  <button
                    onClick={() => onSyncSource(source.id)}
                    className="text-xs text-blue-500 hover:underline"
                  >
                    Sync
                  </button>
                </div>
              ))}
            </div>
          )}

          {!showAddForm ? (
            <button
              onClick={() => setShowAddForm(true)}
              className="w-full p-2 border-2 border-dashed rounded text-gray-500 hover:border-blue-500 hover:text-blue-500 text-sm"
            >
              + Add Calendar (iCal URL)
            </button>
          ) : (
            <div className="p-3 border rounded space-y-3">
              <input
                type="text"
                placeholder="Calendar name"
                value={newSource.name}
                onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                className="w-full p-2 border rounded text-sm"
              />
              <input
                type="url"
                placeholder="iCal URL (ends in .ics)"
                value={newSource.url}
                onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                className="w-full p-2 border rounded text-sm"
              />
              <div>
                <label className="text-xs text-gray-500">Color</label>
                <div className="flex gap-2 mt-1">
                  {colorOptions.map((color) => (
                    <button
                      key={color}
                      onClick={() => setNewSource({ ...newSource, color })}
                      className={`w-6 h-6 rounded-full ${
                        newSource.color === color ? 'ring-2 ring-offset-2 ring-gray-400' : ''
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleAdd}
                  className="flex-1 bg-blue-500 text-white py-2 rounded text-sm hover:bg-blue-600"
                >
                  Add
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 bg-gray-100 py-2 rounded text-sm hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded">
          <p className="font-medium mb-1">How to get your calendar URL:</p>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Google Calendar:</strong> Settings → Calendar → Integrate → Secret address in iCal format</li>
            <li><strong>Outlook:</strong> Settings → Calendar → Shared calendars → Publish</li>
            <li><strong>Apple Calendar:</strong> Right-click calendar → Share → Public Calendar</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
```

### 6. React Hook

#### frontend/src/hooks/useCalendar.js:
```javascript
import { useState, useCallback } from 'react';
import api from '../services/api';

export function useCalendar() {
  const [events, setEvents] = useState({});
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchSources = useCallback(async () => {
    try {
      const response = await api.get('/calendar/sources');
      setSources(response.data);
    } catch (err) {
      console.error('Failed to fetch calendar sources:', err);
    }
  }, []);

  const fetchMonthEvents = useCallback(async (year, month) => {
    try {
      setLoading(true);
      const response = await api.get(`/calendar/events/month/${year}/${month}`);
      setEvents(response.data.events || {});
    } catch (err) {
      console.error('Failed to fetch events:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addSource = async (sourceData) => {
    try {
      const response = await api.post('/calendar/sources', sourceData);
      setSources(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const syncSource = async (sourceId) => {
    try {
      await api.post(`/calendar/sources/${sourceId}/sync`);
      await fetchSources();
    } catch (err) {
      throw err;
    }
  };

  const deleteSource = async (sourceId) => {
    try {
      await api.delete(`/calendar/sources/${sourceId}`);
      setSources(prev => prev.filter(s => s.id !== sourceId));
    } catch (err) {
      throw err;
    }
  };

  return {
    events,
    sources,
    loading,
    fetchSources,
    fetchMonthEvents,
    addSource,
    syncSource,
    deleteSource
  };
}
```

## Dependencies to Add

### backend/requirements.txt (additions):
```
icalendar>=5.0.0
python-dateutil>=2.8.0
```

## Unit Tests

### tests/test_calendar_service.py:
```python
import pytest
from datetime import datetime
from app.services.calendar_service import ICalService

SAMPLE_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test-event-1
SUMMARY:Test Event
DTSTART:20240115T100000Z
DTEND:20240115T110000Z
LOCATION:Conference Room
DESCRIPTION:Test description
END:VEVENT
BEGIN:VEVENT
UID:test-event-2
SUMMARY:All Day Event
DTSTART;VALUE=DATE:20240116
DTEND;VALUE=DATE:20240117
END:VEVENT
END:VCALENDAR"""

class TestICalService:
    def test_parse_ical_basic_event(self):
        service = ICalService()
        events = service.parse_ical(SAMPLE_ICAL)

        assert len(events) == 2

        # Check first event
        event1 = events[0]
        assert event1["title"] == "Test Event"
        assert event1["location"] == "Conference Room"
        assert event1["all_day"] == False

    def test_parse_ical_all_day_event(self):
        service = ICalService()
        events = service.parse_ical(SAMPLE_ICAL)

        # Check all-day event
        event2 = events[1]
        assert event2["title"] == "All Day Event"
        assert event2["all_day"] == True

    def test_parse_ical_empty(self):
        service = ICalService()
        events = service.parse_ical("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR")

        assert len(events) == 0
```

## Acceptance Criteria
- [ ] Monthly calendar view displays correctly
- [ ] Events show as colored indicators on dates
- [ ] Clicking a date shows events for that day
- [ ] Agenda view shows upcoming events
- [ ] iCal URL can be added as calendar source
- [ ] Calendar sources can be synced manually
- [ ] Multiple calendars with different colors
- [ ] Today is highlighted
- [ ] Navigation between months works
- [ ] Recurring events expand correctly
- [ ] Max 10 calendar sources per user
- [ ] Unit tests pass

## Notes
- iCal parsing handles most standard formats
- Recurring events limited to 50 occurrences per query
- Consider background sync job for automatic updates
- Google Calendar API can be added later for richer integration

## Estimated Time
3-4 hours

## Next Task
Task 015: News Widget
