import asyncio
import httpx
from datetime import datetime, timedelta
from icalendar import Calendar
import recurring_ical_events
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from zoneinfo import ZoneInfo

from app.api.v1.deps import CurrentActiveUser

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class CalendarEvent(BaseModel):
    title: str
    start: str  # ISO datetime
    end: str | None  # ISO datetime
    all_day: bool
    location: str | None
    description: str | None
    source: str  # Calendar source name
    source_index: int  # Index of calendar in the list (for color-coding)


class CalendarResponse(BaseModel):
    events: list[CalendarEvent]
    view: str  # "today", "week", "month"
    start_date: str  # ISO date
    end_date: str  # ISO date
    cached: bool = False


# Calendar colors (10 distinct colors for up to 10 calendars)
CALENDAR_COLORS = [
    "#3b82f6",  # Blue
    "#10b981",  # Green
    "#f59e0b",  # Amber
    "#ef4444",  # Red
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#14b8a6",  # Teal
    "#f97316",  # Orange
    "#6366f1",  # Indigo
    "#84cc16",  # Lime
]


# In-memory cache
_calendar_cache: dict[str, tuple[CalendarResponse, datetime]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes


def get_cache_key(calendars: str, view: str, month: str | None) -> str:
    """Generate cache key from parameters."""
    key = f"cal_{calendars}_{view}"
    if month:
        key += f"_{month}"
    return key


def get_cached_calendar(cache_key: str) -> CalendarResponse | None:
    """Get calendar from cache if not expired."""
    if cache_key in _calendar_cache:
        cached_response, cached_time = _calendar_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=CACHE_TTL_SECONDS):
            cached_response.cached = True
            return cached_response
        del _calendar_cache[cache_key]
    return None


def cache_calendar(cache_key: str, response: CalendarResponse):
    """Store calendar in cache."""
    _calendar_cache[cache_key] = (response, datetime.now())


async def fetch_ics_calendar(url: str, source_name: str, source_index: int, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
    """Fetch and parse ICS calendar from URL, expanding recurring events."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0, follow_redirects=True)
            resp.raise_for_status()
            content = resp.text
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Calendar request timed out: {source_name}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch calendar {source_name}: {str(e)}")

    try:
        cal = Calendar.from_ical(content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse calendar {source_name}: {str(e)}")

    events = []

    try:
        # Use recurring_ical_events to expand recurring events within the date range
        # Convert datetime to date for the library
        recurring_events = recurring_ical_events.of(cal).between(start_date, end_date)

        for component in recurring_events:
            try:
                # Get event properties
                summary = str(component.get('summary', 'Untitled'))
                start = component.get('dtstart')
                end = component.get('dtend')
                location = component.get('location')
                description = component.get('description')

                if not start:
                    continue  # Skip events without start time

                # Handle datetime vs date (all-day events)
                start_dt = start.dt
                all_day = False

                if isinstance(start_dt, datetime):
                    # Regular event with time
                    # Ensure timezone-aware
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo('UTC'))
                    start_iso = start_dt.isoformat()
                else:
                    # All-day event (date only)
                    all_day = True
                    start_iso = start_dt.isoformat()

                # Handle end time
                end_iso = None
                if end:
                    end_dt = end.dt
                    if isinstance(end_dt, datetime):
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=ZoneInfo('UTC'))
                        end_iso = end_dt.isoformat()
                    else:
                        end_iso = end_dt.isoformat()

                events.append(CalendarEvent(
                    title=summary,
                    start=start_iso,
                    end=end_iso,
                    all_day=all_day,
                    location=str(location) if location else None,
                    description=str(description) if description else None,
                    source=source_name,
                    source_index=source_index,
                ))

            except Exception as e:
                # Skip malformed events
                continue

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to expand recurring events for {source_name}: {str(e)}")

    return events


def filter_events_by_date_range(
    events: list[CalendarEvent],
    start_date: datetime,
    end_date: datetime,
) -> list[CalendarEvent]:
    """Filter events to those within the date range."""
    filtered = []
    for event in events:
        try:
            # Parse event start time
            if event.all_day:
                # All-day event (date only)
                from datetime import date
                event_start = datetime.fromisoformat(event.start)
                if isinstance(event_start, datetime):
                    event_date = event_start.date()
                else:
                    event_date = event_start
                # Check if event date falls within range
                if start_date.date() <= event_date <= end_date.date():
                    filtered.append(event)
            else:
                # Regular event with time
                event_start = datetime.fromisoformat(event.start)
                # Make timezone-naive for comparison (use local time)
                if event_start.tzinfo:
                    event_start = event_start.replace(tzinfo=None)
                # Check if event starts within range (or is ongoing)
                if start_date <= event_start <= end_date:
                    filtered.append(event)
                elif event.end:
                    # Check if event is ongoing (started before range, ends during range)
                    event_end = datetime.fromisoformat(event.end)
                    if event_end.tzinfo:
                        event_end = event_end.replace(tzinfo=None)
                    if event_start < start_date and event_end > start_date:
                        filtered.append(event)
        except Exception:
            # Skip events with invalid dates
            continue

    return filtered


@router.get("", response_model=CalendarResponse)
async def get_calendar(
    current_user: CurrentActiveUser,
    calendars: str = Query(..., description="Comma-separated ICS URLs"),
    view: str = Query("week", description="View: 'today', 'week', or 'month'"),
    month: Optional[str] = Query(None, description="Month for month view (YYYY-MM)"),
):
    """Fetch calendar events from ICS/iCal URLs.

    Supports multiple calendars by passing comma-separated URLs.
    Events are color-coded by source (calendar index).
    """

    # DEBUG: Log API call details for Insomnia testing
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("CALENDAR API CALL - Copy this for Insomnia:")
    logger.info(f"Method: GET")
    logger.info(f"URL: http://localhost:8000/api/v1/calendar")
    logger.info(f"Query Parameters:")
    logger.info(f"  calendars: {calendars}")
    logger.info(f"  view: {view}")
    if month:
        logger.info(f"  month: {month}")
    logger.info(f"Headers:")
    logger.info(f"  Authorization: Bearer <your_token>")
    logger.info(f"\nFull URL for Insomnia:")
    full_url = f"http://localhost:8000/api/v1/calendar?calendars={calendars}&view={view}"
    if month:
        full_url += f"&month={month}"
    logger.info(full_url)
    logger.info("=" * 80)

    # Generate cache key
    cache_key = get_cache_key(calendars, view, month)

    # Check cache
    cached = get_cached_calendar(cache_key)
    if cached:
        return cached

    # Parse calendar URLs and names
    calendar_list = []
    for i, cal_url in enumerate(calendars.split(",")):
        cal_url = cal_url.strip()
        if cal_url:
            # Extract calendar name from URL or use index
            source_name = f"Calendar {i + 1}"
            if "calendar.google.com" in cal_url:
                source_name = f"Google Calendar {i + 1}"
            elif "outlook" in cal_url.lower():
                source_name = f"Outlook {i + 1}"
            elif "icloud" in cal_url.lower():
                source_name = f"iCloud {i + 1}"

            calendar_list.append((cal_url, source_name, i))

    if not calendar_list:
        raise HTTPException(status_code=400, detail="At least one calendar URL required")

    # Determine date range based on view
    now = datetime.now()
    if view == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif view == "week":
        # This week (Monday to Sunday)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date -= timedelta(days=start_date.weekday())  # Monday
        end_date = start_date + timedelta(days=7)
    elif view == "month":
        if month:
            # Parse specific month
            try:
                year, month_num = map(int, month.split("-"))
                start_date = datetime(year, month_num, 1)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail="Invalid month format (use YYYY-MM)")
        else:
            # Current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # End of month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
    else:
        raise HTTPException(status_code=400, detail="Invalid view (use 'today', 'week', or 'month')")

    # Fetch all calendars in parallel, passing date range for recurring event expansion
    try:
        tasks = [
            fetch_ics_calendar(url, name, idx, start_date, end_date)
            for url, name, idx in calendar_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch calendars: {str(e)}")

    # Collect events from all calendars
    all_events = []
    for result in results:
        if isinstance(result, Exception):
            # Log error but continue with other calendars
            continue
        all_events.extend(result)

    # Filter events by date range
    filtered_events = filter_events_by_date_range(all_events, start_date, end_date)

    # Sort events by start time
    filtered_events.sort(key=lambda e: e.start)

    response = CalendarResponse(
        events=filtered_events,
        view=view,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        cached=False,
    )

    # DEBUG: Log response summary
    logger.info(f"RESPONSE: Returning {len(filtered_events)} events for {start_date.date()} to {end_date.date()}")
    if filtered_events:
        logger.info(f"Events returned:")
        for event in filtered_events[:10]:  # Show first 10
            logger.info(f"  - {event.title}: {event.start} (source: {event.source})")
        if len(filtered_events) > 10:
            logger.info(f"  ... and {len(filtered_events) - 10} more events")
    else:
        logger.info(f"  No events found in date range")
    logger.info("=" * 80)

    # Cache the response
    cache_calendar(cache_key, response)

    return response
