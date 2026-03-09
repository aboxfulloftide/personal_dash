import httpx
import math
import pymysql
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import CurrentActiveUser
from app.core.config import settings

router = APIRouter(prefix="/weather", tags=["Weather"])


class LocationResult(BaseModel):
    id: int
    name: str
    admin1: str | None  # State/Province
    country: str
    country_code: str
    latitude: float
    longitude: float
    population: int | None


class CurrentWeather(BaseModel):
    temp: float | None
    feels_like: float | None
    humidity: int | None
    description: str | None
    icon: str


class HourlyForecast(BaseModel):
    time: str  # "9 AM", "12 PM", etc.
    temp: float | None
    precip_chance: int | None  # percentage
    icon: str


class ForecastDay(BaseModel):
    date: str  # ISO date "2026-02-06"
    day: str   # "Thu", "Fri", etc.
    high: float | None
    low: float | None
    icon: str
    hourly: list[HourlyForecast] = []


class SunTimes(BaseModel):
    sunrise: str  # "6:45 AM"
    sunset: str   # "5:32 PM"
    sunrise_timestamp: int  # Unix timestamp for progress bar calculation
    sunset_timestamp: int   # Unix timestamp for progress bar calculation


class MoonPhase(BaseModel):
    phase_name: str       # "Waxing Gibbous", "Full Moon", etc.
    illumination: int     # 0-100 percentage
    phase_value: float    # 0.0-1.0 (for debugging/future use)


class RadarFrame(BaseModel):
    time: int  # Unix timestamp
    path: str  # Tile URL path


class RadarResponse(BaseModel):
    frames: list[RadarFrame]
    host: str  # Tile server host


class WeatherAlert(BaseModel):
    """Schema for severe weather alert."""
    id: str  # NWS alert ID
    event: str  # "Tornado Warning", "Severe Thunderstorm Watch", etc.
    severity: str  # "Extreme", "Severe", "Moderate", "Minor"
    urgency: str  # "Immediate", "Expected", "Future"
    headline: str  # Brief summary
    description: str  # Full alert text
    instruction: str | None  # Safety instructions
    affected_areas: str  # Human-readable area description
    onset: str  # ISO datetime
    expires: str  # ISO datetime
    geometry: dict | None  # GeoJSON geometry (Polygon/MultiPolygon)


class WeatherAlertsResponse(BaseModel):
    """Schema for weather alerts response."""
    alerts: list[WeatherAlert]
    alert_count: int
    highest_severity: str | None  # For quick checks


class ClimateEvent(BaseModel):
    event_name: str  # Human-readable name
    days_until: int  # Days from today until the average occurrence
    description: str


class WeatherResponse(BaseModel):
    location: str
    current: CurrentWeather
    forecast: list[ForecastDay]
    today_hourly: list[HourlyForecast] = []  # Remaining hours for today
    external_forecast_url: str  # URL to external detailed forecast
    sun_times: SunTimes | None = None  # Sunrise/sunset times
    moon_phase: MoonPhase | None = None  # Current moon phase
    next_climate_event: ClimateEvent | None = None  # Next upcoming climate milestone


# Weather code mappings for Open-Meteo
# https://open-meteo.com/en/docs
WMO_CODE_TO_ICON = {
    0: "sunny",           # Clear sky
    1: "sunny",           # Mainly clear
    2: "partly_cloudy",   # Partly cloudy
    3: "cloudy",          # Overcast
    45: "cloudy",         # Fog
    48: "cloudy",         # Depositing rime fog
    51: "rainy",          # Light drizzle
    53: "rainy",          # Moderate drizzle
    55: "rainy",          # Dense drizzle
    61: "rainy",          # Slight rain
    63: "rainy",          # Moderate rain
    65: "rainy",          # Heavy rain
    71: "snowy",          # Slight snow
    73: "snowy",          # Moderate snow
    75: "snowy",          # Heavy snow
    80: "rainy",          # Slight rain showers
    81: "rainy",          # Moderate rain showers
    82: "rainy",          # Violent rain showers
    85: "snowy",          # Slight snow showers
    86: "snowy",          # Heavy snow showers
    95: "stormy",         # Thunderstorm
    96: "stormy",         # Thunderstorm with slight hail
    99: "stormy",         # Thunderstorm with heavy hail
}

WMO_CODE_TO_DESC = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Foggy",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm",
}


async def search_locations(query: str, count: int = 10) -> list[LocationResult]:
    """Search for locations using Open-Meteo geocoding."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count={count}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append(LocationResult(
            id=item["id"],
            name=item["name"],
            admin1=item.get("admin1"),
            country=item.get("country", ""),
            country_code=item.get("country_code", ""),
            latitude=item["latitude"],
            longitude=item["longitude"],
            population=item.get("population"),
        ))
    return results


async def geocode_location(location: str) -> tuple[float, float, str]:
    """Convert location name to coordinates using Open-Meteo geocoding."""
    # Check if location looks like coordinates (lat,lon)
    if "," in location:
        parts = location.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Valid coordinate range check
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon, f"{lat:.2f}, {lon:.2f}"
            except ValueError:
                pass  # Not coordinates, continue with geocoding

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    results = data.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"Location not found: {location}")

    result = results[0]
    lat = result["latitude"]
    lon = result["longitude"]
    name = result.get("name", location)
    admin = result.get("admin1", "")
    country = result.get("country_code", "")

    if admin:
        display_name = f"{name}, {admin}"
    elif country:
        display_name = f"{name}, {country}"
    else:
        display_name = name

    return lat, lon, display_name


def calculate_moon_phase(dt: datetime | None = None) -> MoonPhase:
    """Calculate current moon phase based on date.

    Uses the lunar synodic month (29.53 days) to calculate phase.
    Reference: January 6, 2000 was a new moon.

    Returns:
        MoonPhase with name, illumination percentage, and phase value (0.0-1.0)
    """
    if dt is None:
        dt = datetime.now()

    # Known new moon: January 6, 2000, 18:14 UTC
    known_new_moon = datetime(2000, 1, 6, 18, 14)

    # Lunar synodic month in days
    lunar_month = 29.530588853

    # Calculate days since known new moon
    days_since = (dt - known_new_moon).total_seconds() / 86400

    # Calculate phase (0.0 = new moon, 0.5 = full moon, 1.0 = new moon)
    phase = (days_since % lunar_month) / lunar_month

    # Calculate illumination percentage
    # Illumination peaks at 100% during full moon (phase = 0.5)
    illumination = int(100 * (1 - abs(2 * (phase - 0.5))))

    # Determine phase name
    # Phase ranges based on typical lunar phase divisions
    if phase < 0.03 or phase >= 0.97:
        phase_name = "New Moon"
    elif phase < 0.22:
        phase_name = "Waxing Crescent"
    elif phase < 0.28:
        phase_name = "First Quarter"
    elif phase < 0.47:
        phase_name = "Waxing Gibbous"
    elif phase < 0.53:
        phase_name = "Full Moon"
    elif phase < 0.72:
        phase_name = "Waning Gibbous"
    elif phase < 0.78:
        phase_name = "Last Quarter"
    else:  # 0.78 to 0.97
        phase_name = "Waning Crescent"

    return MoonPhase(
        phase_name=phase_name,
        illumination=illumination,
        phase_value=round(phase, 3),
    )


def get_external_forecast_url(lat: float, lon: float, provider: str = "windy") -> str:
    """Generate URL for external weather forecast.

    Supported providers:
    - windy: Windy.com - Interactive weather maps (default)
    - wunderground: Weather Underground - Detailed forecasts
    - nws: National Weather Service - US only, official forecasts
    - openweather: OpenWeatherMap - Global coverage
    """
    if provider == "nws":
        # National Weather Service (US only)
        return f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}"
    elif provider == "wunderground":
        # Weather Underground - uses lat,lon format
        return f"https://www.wunderground.com/weather/{lat},{lon}"
    elif provider == "openweather":
        # OpenWeatherMap - weather map with location
        return f"https://openweathermap.org/weathermap?lat={lat}&lon={lon}&zoom=10"
    else:  # Default to windy
        # Windy.com - simplest, works with lat/lon directly
        return f"https://www.windy.com/{lat}/{lon}"


async def fetch_openmeteo(lat: float, lon: float, units: str) -> dict:
    """Fetch weather from Open-Meteo API."""
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset"
        f"&hourly=temperature_2m,precipitation_probability,weather_code"
        f"&temperature_unit={temp_unit}"
        f"&timezone=auto"
        f"&forecast_days=5"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    current_data = data.get("current", {})
    daily_data = data.get("daily", {})
    hourly_data = data.get("hourly", {})

    weather_code = current_data.get("weather_code", 0)

    current = CurrentWeather(
        temp=current_data.get("temperature_2m"),
        feels_like=current_data.get("apparent_temperature"),
        humidity=current_data.get("relative_humidity_2m"),
        description=WMO_CODE_TO_DESC.get(weather_code, "Unknown"),
        icon=WMO_CODE_TO_ICON.get(weather_code, "cloudy"),
    )

    # Parse hourly data and group by date
    hourly_times = hourly_data.get("time", [])
    hourly_temps = hourly_data.get("temperature_2m", [])
    hourly_precip = hourly_data.get("precipitation_probability", [])
    hourly_codes = hourly_data.get("weather_code", [])

    # Group hourly data by date, storing (hour, item) tuples
    hourly_by_date: dict[str, list[tuple[int, HourlyForecast]]] = {}
    now = datetime.now()

    for i, time_str in enumerate(hourly_times):
        dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
        date_key = dt.strftime("%Y-%m-%d")

        # Only include every 2 hours for cleaner display
        if dt.hour % 2 != 0:
            continue

        code = hourly_codes[i] if i < len(hourly_codes) else 0
        # Format time string - use %I with lstrip to handle both platforms
        hour_12 = dt.strftime("%I %p").lstrip("0")  # "9 AM", "12 PM"
        hourly_item = HourlyForecast(
            time=hour_12,
            temp=hourly_temps[i] if i < len(hourly_temps) else None,
            precip_chance=hourly_precip[i] if i < len(hourly_precip) else None,
            icon=WMO_CODE_TO_ICON.get(code, "cloudy"),
        )

        if date_key not in hourly_by_date:
            hourly_by_date[date_key] = []
        hourly_by_date[date_key].append((dt.hour, hourly_item))

    # Build forecast with hourly data
    forecast = []
    times = daily_data.get("time", [])
    highs = daily_data.get("temperature_2m_max", [])
    lows = daily_data.get("temperature_2m_min", [])
    codes = daily_data.get("weather_code", [])

    for i, date_str in enumerate(times[:5]):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        code = codes[i] if i < len(codes) else 0
        # Extract just the HourlyForecast items from (hour, item) tuples
        day_hourly = [item for _, item in hourly_by_date.get(date_str, [])]
        forecast.append(ForecastDay(
            date=date_str,
            day=date.strftime("%a"),
            high=highs[i] if i < len(highs) else None,
            low=lows[i] if i < len(lows) else None,
            icon=WMO_CODE_TO_ICON.get(code, "cloudy"),
            hourly=day_hourly,
        ))

    # Get extended hourly forecast from current hour through midnight
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    current_hour = now.hour
    today_hourly = []

    # Add remaining hours from today (using stored hour from tuple)
    for hour, item in hourly_by_date.get(today_str, []):
        if hour >= current_hour:
            today_hourly.append(item)

    # Add midnight (12 AM) from tomorrow to show end of day
    for hour, item in hourly_by_date.get(tomorrow_str, []):
        if hour == 0:  # Midnight
            today_hourly.append(item)
            break

    # Parse sunrise/sunset times for today
    sun_times = None
    sunrise_times = daily_data.get("sunrise", [])
    sunset_times = daily_data.get("sunset", [])
    if sunrise_times and sunset_times:
        try:
            # Parse today's sunrise/sunset (first entry)
            sunrise_dt = datetime.strptime(sunrise_times[0], "%Y-%m-%dT%H:%M")
            sunset_dt = datetime.strptime(sunset_times[0], "%Y-%m-%dT%H:%M")

            sun_times = SunTimes(
                sunrise=sunrise_dt.strftime("%I:%M %p").lstrip("0"),  # "6:45 AM"
                sunset=sunset_dt.strftime("%I:%M %p").lstrip("0"),    # "5:32 PM"
                sunrise_timestamp=int(sunrise_dt.timestamp()),
                sunset_timestamp=int(sunset_dt.timestamp()),
            )
        except (ValueError, IndexError):
            pass  # If parsing fails, sun_times remains None

    return {"current": current, "forecast": forecast, "today_hourly": today_hourly, "sun_times": sun_times}


async def fetch_openweathermap(lat: float, lon: float, units: str, api_key: str) -> dict:
    """Fetch weather from OpenWeatherMap API."""
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required for OpenWeatherMap")

    # Current weather
    current_url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&units={units}&appid={api_key}"
    )

    # 5-day forecast
    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&units={units}&appid={api_key}"
    )

    async with httpx.AsyncClient() as client:
        current_resp = await client.get(current_url, timeout=10.0)
        if current_resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid OpenWeatherMap API key")
        current_data = current_resp.json()

        forecast_resp = await client.get(forecast_url, timeout=10.0)
        forecast_data = forecast_resp.json()

    # Map OWM icon codes to our icons
    def owm_to_icon(icon_code: str) -> str:
        if icon_code.startswith("01"):
            return "sunny"
        elif icon_code.startswith("02"):
            return "partly_cloudy"
        elif icon_code.startswith("03") or icon_code.startswith("04"):
            return "cloudy"
        elif icon_code.startswith("09") or icon_code.startswith("10"):
            return "rainy"
        elif icon_code.startswith("11"):
            return "stormy"
        elif icon_code.startswith("13"):
            return "snowy"
        else:
            return "cloudy"

    main = current_data.get("main", {})
    weather = current_data.get("weather", [{}])[0]

    current = CurrentWeather(
        temp=main.get("temp"),
        feels_like=main.get("feels_like"),
        humidity=main.get("humidity"),
        description=weather.get("description", "").capitalize(),
        icon=owm_to_icon(weather.get("icon", "")),
    )

    # Process forecast - get one entry per day
    forecast = []
    seen_days = set()
    for item in forecast_data.get("list", []):
        date = datetime.fromtimestamp(item["dt"])
        day_name = date.strftime("%a")
        if day_name in seen_days:
            continue
        seen_days.add(day_name)

        item_main = item.get("main", {})
        item_weather = item.get("weather", [{}])[0]

        forecast.append(ForecastDay(
            day=day_name,
            high=item_main.get("temp_max"),
            low=item_main.get("temp_min"),
            icon=owm_to_icon(item_weather.get("icon", "")),
        ))

        if len(forecast) >= 5:
            break

    return {"current": current, "forecast": forecast}


async def fetch_nws_alerts(lat: float, lon: float) -> WeatherAlertsResponse:
    """Fetch active weather alerts from National Weather Service.

    US locations only. Returns empty list for non-US locations or API failures.
    """
    url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"

    try:
        async with httpx.AsyncClient() as client:
            # NWS requires User-Agent header
            headers = {"User-Agent": "(PersonalDash, dashboard@example.com)"}
            resp = await client.get(url, timeout=10.0, headers=headers)

            if resp.status_code != 200:
                logger.warning(f"NWS alerts API returned {resp.status_code} for {lat},{lon}")
                return WeatherAlertsResponse(alerts=[], alert_count=0, highest_severity=None)

            data = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch NWS alerts: {e}")
        return WeatherAlertsResponse(alerts=[], alert_count=0, highest_severity=None)

    alerts = []
    severities = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry")

        alert = WeatherAlert(
            id=props.get("id", ""),
            event=props.get("event", "Unknown"),
            severity=props.get("severity", "Unknown"),
            urgency=props.get("urgency", "Unknown"),
            headline=props.get("headline", ""),
            description=props.get("description", ""),
            instruction=props.get("instruction"),
            affected_areas=props.get("areaDesc", ""),
            onset=props.get("onset", ""),
            expires=props.get("expires", ""),
            geometry=geometry,  # Pass through GeoJSON
        )
        alerts.append(alert)
        severities.append(props.get("severity", "Unknown"))

    # Determine highest severity
    severity_order = ["Extreme", "Severe", "Moderate", "Minor"]
    highest = None
    for sev in severity_order:
        if sev in severities:
            highest = sev
            break

    return WeatherAlertsResponse(
        alerts=alerts,
        alert_count=len(alerts),
        highest_severity=highest,
    )


def _format_event_name(raw_name: str) -> str:
    """Convert DB event names like 'first_70F_day' to readable labels like 'First 70°F Day'."""
    name = raw_name.replace("_", " ")
    # Replace temperature patterns: 70F -> 70°F, 32F -> 32°F
    import re
    name = re.sub(r'(\d+)F\b', r'\1°F', name, flags=re.IGNORECASE)
    # Title case but keep °F intact
    words = name.split()
    result = []
    for w in words:
        if '°' in w:
            result.append(w)
        else:
            result.append(w.capitalize())
    return " ".join(result)


def fetch_next_climate_event() -> ClimateEvent | None:
    """Query the weather database for the next upcoming climate event."""
    if not settings.WEATHER_DB_URL:
        return None

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.WEATHER_DB_URL, pool_pre_ping=True)
        today_doy = datetime.now().timetuple().tm_yday

        with engine.connect() as conn:
            # Find the next event after today's day-of-year
            result = conn.execute(text(
                "SELECT event_name, avg_day_of_year, description "
                "FROM climate_averages "
                "WHERE avg_day_of_year > :today_doy "
                "ORDER BY avg_day_of_year ASC LIMIT 1"
            ), {"today_doy": today_doy})
            row = result.fetchone()

            if not row:
                # Wrap around to next year's first event
                result = conn.execute(text(
                    "SELECT event_name, avg_day_of_year, description "
                    "FROM climate_averages "
                    "ORDER BY avg_day_of_year ASC LIMIT 1"
                ))
                row = result.fetchone()
                if not row:
                    return None
                days_until = int(365 - today_doy + float(row[1]))
            else:
                days_until = int(float(row[1]) - today_doy)

        engine.dispose()

        return ClimateEvent(
            event_name=_format_event_name(row[0]),
            days_until=days_until,
            description=row[2] or "",
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to fetch climate event: {e}")
        return None


@router.get("/locations/search", response_model=list[LocationResult])
async def search_locations_endpoint(
    current_user: CurrentActiveUser,
    q: str = Query(..., min_length=2, description="Search query"),
):
    """Search for locations by name. Returns matching cities with coordinates."""
    try:
        results = await search_locations(q)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to search locations")

    if not results:
        raise HTTPException(status_code=404, detail=f"No locations found for: {q}")

    return results


@router.get("/radar", response_model=RadarResponse)
async def get_weather_radar(
    current_user: CurrentActiveUser,
):
    """Fetch weather radar data from RainViewer API.

    Returns animated radar frames for the past ~2 hours.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10.0)
            data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch radar data: {str(e)}")

    # Extract radar frames (past precipitation)
    radar_frames = data.get("radar", {}).get("past", [])
    if not radar_frames:
        raise HTTPException(status_code=404, detail="No radar data available")

    # Get the tile server host
    host = data.get("host", "")

    # Build frame list with timestamps and paths
    frames = [
        RadarFrame(time=frame["time"], path=frame["path"])
        for frame in radar_frames
    ]

    return RadarResponse(frames=frames, host=host)


@router.get("/alerts", response_model=WeatherAlertsResponse)
async def get_weather_alerts(
    current_user: CurrentActiveUser,
    location: str = Query(..., description="City name or lat,lon coordinates"),
):
    """
    Get active severe weather alerts for a location from National Weather Service.

    US locations only. Returns empty list for non-US locations.
    """
    try:
        lat, lon, _ = await geocode_location(location)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to geocode location")

    alerts = await fetch_nws_alerts(lat, lon)
    return alerts


@router.get("", response_model=WeatherResponse)
async def get_weather(
    current_user: CurrentActiveUser,
    location: str = Query(..., description="City name or location"),
    units: str = Query("imperial", description="imperial or metric"),
    provider: str = Query("openmeteo", description="Weather API provider"),
    api_key: str | None = Query(None, description="API key for OpenWeatherMap"),
    external_forecast_provider: str = Query("windy", description="External forecast link provider (windy, wunderground, nws, openweather)"),
):
    """Fetch current weather and forecast for a location."""
    try:
        lat, lon, display_name = await geocode_location(location)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to geocode location")

    try:
        if provider == "openweathermap":
            result = await fetch_openweathermap(lat, lon, units, api_key or "")
        else:
            result = await fetch_openmeteo(lat, lon, units)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch weather: {str(e)}")

    # Calculate moon phase
    moon_phase = calculate_moon_phase()

    # Fetch next climate milestone
    next_climate_event = fetch_next_climate_event()

    return WeatherResponse(
        location=display_name,
        current=result["current"],
        forecast=result["forecast"],
        today_hourly=result.get("today_hourly", []),
        external_forecast_url=get_external_forecast_url(lat, lon, external_forecast_provider),
        sun_times=result.get("sun_times"),
        moon_phase=moon_phase,
        next_climate_event=next_climate_event,
    )
