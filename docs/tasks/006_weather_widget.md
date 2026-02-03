# Task 006: Weather Widget

## Objective
Build the Weather widget using Open-Meteo API (free, no API key required) to display current conditions and forecast.

## Prerequisites
- Task 005 completed
- Dashboard layout working

## API Information
- **API**: Open-Meteo (https://open-meteo.com/)
- **Cost**: Free, no API key required
- **Rate Limit**: 10,000 requests/day
- **Documentation**: https://open-meteo.com/en/docs

## Deliverables

### 1. Backend Weather Service

#### app/services/weather_service.py:
```python
import httpx
from datetime import datetime, timedelta
from typing import Optional
from app.core.cache import cache_get, cache_set

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1"
CACHE_TTL = 1800  # 30 minutes

# Weather code to description mapping
WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌧️"),
    53: ("Moderate drizzle", "🌧️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌨️"),
    67: ("Heavy freezing rain", "🌨️"),
    71: ("Slight snow", "❄️"),
    73: ("Moderate snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌦️"),
    82: ("Violent rain showers", "🌦️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

def get_weather_description(code: int) -> tuple:
    return WEATHER_CODES.get(code, ("Unknown", "❓"))

async def geocode_location(query: str) -> Optional[dict]:
    """Convert location name to coordinates."""
    cache_key = f"geocode:{query.lower()}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GEOCODING_BASE}/search",
            params={"name": query, "count": 1, "language": "en", "format": "json"}
        )

        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get("results"):
            return None

        result = data["results"][0]
        location = {
            "name": result.get("name"),
            "country": result.get("country"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "timezone": result.get("timezone")
        }

        await cache_set(cache_key, location, ttl=86400)  # Cache for 24 hours
        return location

async def get_weather(latitude: float, longitude: float, units: str = "imperial") -> Optional[dict]:
    """Get current weather and forecast."""
    cache_key = f"weather:{latitude}:{longitude}:{units}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "timezone": "auto",
        "forecast_days": 7
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{OPEN_METEO_BASE}/forecast", params=params)

        if response.status_code != 200:
            return None

        data = response.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        weather_code = current.get("weather_code", 0)
        description, icon = get_weather_description(weather_code)

        result = {
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "weather_code": weather_code,
                "description": description,
                "icon": icon
            },
            "forecast": [],
            "units": {
                "temperature": "°F" if units == "imperial" else "°C",
                "wind": "mph" if units == "imperial" else "km/h"
            }
        }

        # Process daily forecast
        dates = daily.get("time", [])
        for i, date in enumerate(dates[:7]):
            code = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            desc, ico = get_weather_description(code)
            result["forecast"].append({
                "date": date,
                "day": datetime.strptime(date, "%Y-%m-%d").strftime("%a"),
                "high": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "low": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "precipitation_chance": daily.get("precipitation_probability_max", [])[i] if i < len(daily.get("precipitation_probability_max", [])) else None,
                "description": desc,
                "icon": ico
            })

        await cache_set(cache_key, result, ttl=CACHE_TTL)
        return result
```

### 2. Simple Cache Implementation

#### app/core/cache.py:
```python
from typing import Any, Optional
from datetime import datetime, timedelta
import json

# Simple in-memory cache (replace with Redis in production)
_cache: dict = {}

async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    if key in _cache:
        item = _cache[key]
        if item["expires"] > datetime.now():
            return item["value"]
        else:
            del _cache[key]
    return None

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL in seconds."""
    _cache[key] = {
        "value": value,
        "expires": datetime.now() + timedelta(seconds=ttl)
    }

async def cache_delete(key: str) -> None:
    """Delete value from cache."""
    if key in _cache:
        del _cache[key]

def cache_clear() -> None:
    """Clear all cache."""
    _cache.clear()
```

### 3. Weather API Endpoints

#### app/api/v1/endpoints/weather.py:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.weather_service import geocode_location, get_weather

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/search")
async def search_location(
    q: str = Query(..., min_length=2, description="Location search query"),
    current_user: User = Depends(get_current_user)
):
    """Search for a location by name."""
    location = await geocode_location(q)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.get("/forecast")
async def get_forecast(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    units: str = Query("imperial", regex="^(imperial|metric)$"),
    current_user: User = Depends(get_current_user)
):
    """Get weather forecast for coordinates."""
    weather = await get_weather(lat, lon, units)
    if not weather:
        raise HTTPException(status_code=503, detail="Weather service unavailable")
    return weather
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, weather

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weather.router)
```

### 4. Frontend Weather Widget

#### src/components/widgets/WeatherWidget.jsx:
```jsx
import { useState, useEffect } from 'react';
import api from '../../services/api';

export default function WeatherWidget({ config }) {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSetup, setShowSetup] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  const location = config.location;
  const units = config.units || 'imperial';

  useEffect(() => {
    if (location?.latitude && location?.longitude) {
      fetchWeather();
    } else {
      setShowSetup(true);
      setLoading(false);
    }
  }, [location, units]);

  const fetchWeather = async () => {
    if (!location?.latitude || !location?.longitude) return;

    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/weather/forecast', {
        params: {
          lat: location.latitude,
          lon: location.longitude,
          units
        }
      });
      setWeather(response.data);
      setShowSetup(false);
    } catch (err) {
      setError('Failed to load weather');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const response = await api.get('/weather/search', {
        params: { q: searchQuery }
      });

      // This would need to trigger a config update through parent
      // For now, we'll store in local state and show weather
      const newLocation = response.data;
      config.location = newLocation;
      config.onConfigChange?.({ location: newLocation });

      setShowSetup(false);
      fetchWeather();
    } catch (err) {
      setError('Location not found');
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (showSetup || !weather) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <span className="text-4xl mb-3">🌤️</span>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 text-center">
          Enter a location to get weather
        </p>
        <form onSubmit={handleSearch} className="w-full max-w-xs">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="City name..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm mb-2"
          />
          <button
            type="submit"
            disabled={searching}
            className="w-full px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Set Location'}
          </button>
        </form>
        {error && (
          <p className="text-red-500 text-xs mt-2">{error}</p>
        )}
      </div>
    );
  }

  const { current, forecast, units: weatherUnits } = weather;

  return (
    <div className="h-full flex flex-col">
      {/* Current Weather */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {Math.round(current.temperature)}{weatherUnits.temperature}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Feels like {Math.round(current.feels_like)}{weatherUnits.temperature}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
            {current.description}
          </div>
        </div>
        <div className="text-5xl">{current.icon}</div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-sm text-gray-600 dark:text-gray-400 mb-4">
        <div>💧 {current.humidity}%</div>
        <div>💨 {Math.round(current.wind_speed)} {weatherUnits.wind}</div>
      </div>

      {/* Location */}
      <div className="text-xs text-gray-400 dark:text-gray-500 mb-3">
        📍 {location?.name}{location?.country ? `, ${location.country}` : ''}
      </div>

      {/* Forecast */}
      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-2 min-w-max">
          {forecast.slice(1, 6).map((day) => (
            <div
              key={day.date}
              className="flex flex-col items-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg min-w-[60px]"
            >
              <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
                {day.day}
              </div>
              <div className="text-xl my-1">{day.icon}</div>
              <div className="text-xs text-gray-900 dark:text-white">
                {Math.round(day.high)}°
              </div>
              <div className="text-xs text-gray-400">
                {Math.round(day.low)}°
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Refresh button */}
      <button
        onClick={fetchWeather}
        className="mt-2 text-xs text-blue-500 hover:text-blue-600 self-end"
      >
        Refresh
      </button>
    </div>
  );
}
```

### 5. Register Weather Widget

#### Update src/components/widgets/widgetRegistry.js:
```javascript
const widgetRegistry = {
  weather: {
    component: () => import('./WeatherWidget'),
    name: 'Weather',
    description: 'Current weather and forecast',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 4 }
  },
  placeholder: {
    component: () => import('./PlaceholderWidget'),
    name: 'Placeholder',
    description: 'Placeholder widget',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 1, h: 1 },
    maxSize: { w: 4, h: 4 }
  }
};

export function getWidget(type) {
  return widgetRegistry[type] || widgetRegistry.placeholder;
}

export function getAvailableWidgets() {
  return Object.entries(widgetRegistry)
    .filter(([type]) => type !== 'placeholder')
    .map(([type, config]) => ({
      type,
      name: config.name,
      description: config.description,
      defaultSize: config.defaultSize
    }));
}

export default widgetRegistry;
```

### 6. Widget Configuration Storage

#### app/models/widget.py (update):
```python
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    layout = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    widget_id = Column(String(100), nullable=False)  # Matches frontend widget id
    widget_type = Column(String(50), nullable=False)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 7. Widget Config Endpoints

#### app/api/v1/endpoints/widgets.py:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.widget import WidgetConfig
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/widgets", tags=["Widgets"])

class WidgetConfigUpdate(BaseModel):
    config: dict

@router.get("/{widget_id}/config")
def get_widget_config(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get widget configuration."""
    config = db.query(WidgetConfig).filter(
        WidgetConfig.user_id == current_user.id,
        WidgetConfig.widget_id == widget_id
    ).first()

    if not config:
        return {"config": {}}

    return {"config": config.config}

@router.put("/{widget_id}/config")
def update_widget_config(
    widget_id: str,
    data: WidgetConfigUpdate,
    widget_type: str = "unknown",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update widget configuration."""
    config = db.query(WidgetConfig).filter(
        WidgetConfig.user_id == current_user.id,
        WidgetConfig.widget_id == widget_id
    ).first()

    if config:
        config.config = data.config
    else:
        config = WidgetConfig(
            user_id=current_user.id,
            widget_id=widget_id,
            widget_type=widget_type,
            config=data.config
        )
        db.add(config)

    db.commit()
    return {"config": config.config}
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, weather, widgets

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weather.router)
api_router.include_router(widgets.router)
```

## Unit Tests

### tests/test_weather.py:
```python
import pytest
from httpx import AsyncClient
from app.services.weather_service import get_weather_description, geocode_location

def test_weather_code_mapping():
    desc, icon = get_weather_description(0)
    assert desc == "Clear sky"
    assert icon == "☀️"

    desc, icon = get_weather_description(95)
    assert desc == "Thunderstorm"
    assert icon == "⛈️"

    desc, icon = get_weather_description(999)
    assert desc == "Unknown"
    assert icon == "❓"

@pytest.mark.asyncio
async def test_geocode_location():
    # Test with a known city
    result = await geocode_location("New York")
    assert result is not None
    assert result["name"] == "New York"
    assert "latitude" in result
    assert "longitude" in result

@pytest.mark.asyncio
async def test_geocode_invalid_location():
    result = await geocode_location("xyznonexistentcity123")
    assert result is None
```

## Acceptance Criteria
- [ ] Weather widget displays in widget list
- [ ] Location search works
- [ ] Current temperature and conditions display
- [ ] 5-day forecast displays
- [ ] Weather icons show correctly
- [ ] Data caches for 30 minutes
- [ ] Error states handled gracefully
- [ ] Widget config persists location
- [ ] Refresh button works
- [ ] Unit tests pass

## Estimated Time
3-4 hours

## Next Task
Task 007: Stock Market Widget
