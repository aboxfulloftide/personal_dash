# Task 012: Weather Widget

## Objective
Build a weather widget that displays current conditions and forecasts using the free Open-Meteo API.

## Prerequisites
- Task 006 completed (Widget Framework)
- Task 003 completed (Database Schema)

## Features
- Current weather conditions
- 7-day forecast
- Multiple location support
- Automatic location detection (optional)
- Temperature unit preference (°F/°C)
- Weather alerts
- Caching to reduce API calls

## API Choice: Open-Meteo
- **Free**: No API key required
- **No rate limits** for reasonable use
- **Global coverage**
- **Reliable** and well-documented

## Deliverables

### 1. Database Models

#### backend/app/models/weather.py:
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class WeatherLocation(Base):
    __tablename__ = "weather_locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(100), nullable=False)  # Display name
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), default="auto")

    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="weather_locations")


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("weather_locations.id"), nullable=False)

    # Cache data as JSON string
    current_weather = Column(String(2000), nullable=True)
    daily_forecast = Column(String(10000), nullable=True)
    hourly_forecast = Column(String(20000), nullable=True)

    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
```

### 2. Weather Service

#### backend/app/services/weather_service.py:
```python
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from sqlalchemy.orm import Session
from app.models.weather import WeatherLocation, WeatherCache
from app.core.config import settings


class OpenMeteoService:
    """Weather service using Open-Meteo API (free, no key required)."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

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
        82: ("Violent rain showers", "⛈️"),
        85: ("Slight snow showers", "🌨️"),
        86: ("Heavy snow showers", "🌨️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with slight hail", "⛈️"),
        99: ("Thunderstorm with heavy hail", "⛈️"),
    }

    def __init__(self):
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes

    async def get_weather(
        self, 
        latitude: float, 
        longitude: float,
        units: str = "fahrenheit"
    ) -> Dict[str, Any]:
        """Fetch current weather and forecast from Open-Meteo."""

        temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation"
            ],
            "hourly": [
                "temperature_2m",
                "weather_code",
                "precipitation_probability"
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "sunrise",
                "sunset"
            ],
            "temperature_unit": temp_unit,
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "forecast_days": 7
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, units)

    def _parse_response(self, data: Dict, units: str) -> Dict[str, Any]:
        """Parse Open-Meteo response into our format."""

        current = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        # Current weather
        weather_code = current.get("weather_code", 0)
        description, icon = self.WEATHER_CODES.get(weather_code, ("Unknown", "❓"))

        current_weather = {
            "temperature": round(current.get("temperature_2m", 0)),
            "feels_like": round(current.get("apparent_temperature", 0)),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": round(current.get("wind_speed_10m", 0)),
            "wind_direction": current.get("wind_direction_10m", 0),
            "precipitation": current.get("precipitation", 0),
            "weather_code": weather_code,
            "description": description,
            "icon": icon,
            "units": units
        }

        # Daily forecast
        daily_forecast = []
        if daily.get("time"):
            for i, date in enumerate(daily["time"]):
                code = daily["weather_code"][i] if daily.get("weather_code") else 0
                desc, ico = self.WEATHER_CODES.get(code, ("Unknown", "❓"))

                daily_forecast.append({
                    "date": date,
                    "temp_max": round(daily["temperature_2m_max"][i]) if daily.get("temperature_2m_max") else None,
                    "temp_min": round(daily["temperature_2m_min"][i]) if daily.get("temperature_2m_min") else None,
                    "precipitation": daily["precipitation_sum"][i] if daily.get("precipitation_sum") else 0,
                    "precipitation_probability": daily["precipitation_probability_max"][i] if daily.get("precipitation_probability_max") else 0,
                    "weather_code": code,
                    "description": desc,
                    "icon": ico,
                    "sunrise": daily["sunrise"][i] if daily.get("sunrise") else None,
                    "sunset": daily["sunset"][i] if daily.get("sunset") else None
                })

        # Hourly forecast (next 24 hours)
        hourly_forecast = []
        if hourly.get("time"):
            now = datetime.utcnow()
            for i, time_str in enumerate(hourly["time"][:24]):
                code = hourly["weather_code"][i] if hourly.get("weather_code") else 0
                desc, ico = self.WEATHER_CODES.get(code, ("Unknown", "❓"))

                hourly_forecast.append({
                    "time": time_str,
                    "temperature": round(hourly["temperature_2m"][i]) if hourly.get("temperature_2m") else None,
                    "precipitation_probability": hourly["precipitation_probability"][i] if hourly.get("precipitation_probability") else 0,
                    "weather_code": code,
                    "icon": ico
                })

        return {
            "current": current_weather,
            "daily": daily_forecast,
            "hourly": hourly_forecast,
            "timezone": data.get("timezone", "UTC"),
            "fetched_at": datetime.utcnow().isoformat()
        }

    async def search_location(self, query: str) -> List[Dict[str, Any]]:
        """Search for locations by name."""

        params = {
            "name": query,
            "count": 10,
            "language": "en",
            "format": "json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.GEOCODING_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "name": item.get("name"),
                "admin1": item.get("admin1"),  # State/Province
                "country": item.get("country"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
                "display_name": f"{item.get('name')}, {item.get('admin1', '')}, {item.get('country', '')}"
            })

        return results


class WeatherService:
    """Main weather service with caching."""

    def __init__(self):
        self.api = OpenMeteoService()
        self.cache_duration = timedelta(minutes=30)

    async def get_weather_for_location(
        self, 
        db: Session, 
        location: WeatherLocation,
        units: str = "fahrenheit",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get weather for a location, using cache if available."""

        # Check cache
        if not force_refresh:
            cache = db.query(WeatherCache).filter(
                WeatherCache.location_id == location.id,
                WeatherCache.expires_at > datetime.utcnow()
            ).first()

            if cache:
                return {
                    "current": json.loads(cache.current_weather) if cache.current_weather else None,
                    "daily": json.loads(cache.daily_forecast) if cache.daily_forecast else None,
                    "hourly": json.loads(cache.hourly_forecast) if cache.hourly_forecast else None,
                    "cached": True,
                    "cached_at": cache.cached_at.isoformat()
                }

        # Fetch fresh data
        weather_data = await self.api.get_weather(
            location.latitude,
            location.longitude,
            units
        )

        # Update cache
        cache = db.query(WeatherCache).filter(
            WeatherCache.location_id == location.id
        ).first()

        if not cache:
            cache = WeatherCache(location_id=location.id)
            db.add(cache)

        cache.current_weather = json.dumps(weather_data["current"])
        cache.daily_forecast = json.dumps(weather_data["daily"])
        cache.hourly_forecast = json.dumps(weather_data["hourly"])
        cache.cached_at = datetime.utcnow()
        cache.expires_at = datetime.utcnow() + self.cache_duration

        db.commit()

        weather_data["cached"] = False
        return weather_data

    async def search_locations(self, query: str) -> List[Dict[str, Any]]:
        """Search for locations."""
        return await self.api.search_location(query)
```

### 3. API Endpoints

#### backend/app/api/v1/weather.py:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.weather import WeatherLocation
from app.schemas.weather import (
    WeatherLocationCreate, WeatherLocationUpdate, 
    WeatherLocationResponse, WeatherResponse, LocationSearchResult
)
from app.api.deps import get_current_user
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])
weather_service = WeatherService()


@router.get("/locations", response_model=List[WeatherLocationResponse])
async def list_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's saved weather locations."""
    locations = db.query(WeatherLocation).filter(
        WeatherLocation.user_id == current_user.id
    ).order_by(WeatherLocation.display_order).all()

    return locations


@router.post("/locations", response_model=WeatherLocationResponse, status_code=status.HTTP_201_CREATED)
async def add_location(
    location_data: WeatherLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new weather location."""
    # Check limit (max 5 locations)
    count = db.query(WeatherLocation).filter(
        WeatherLocation.user_id == current_user.id
    ).count()

    if count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 locations allowed"
        )

    # If this is first location or marked as primary, update others
    if location_data.is_primary or count == 0:
        db.query(WeatherLocation).filter(
            WeatherLocation.user_id == current_user.id
        ).update({"is_primary": False})

    location = WeatherLocation(
        user_id=current_user.id,
        name=location_data.name,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        timezone=location_data.timezone or "auto",
        is_primary=location_data.is_primary or count == 0,
        display_order=count
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a weather location."""
    location = db.query(WeatherLocation).filter(
        WeatherLocation.id == location_id,
        WeatherLocation.user_id == current_user.id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(location)
    db.commit()


@router.put("/locations/{location_id}/primary", response_model=WeatherLocationResponse)
async def set_primary_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set a location as primary."""
    location = db.query(WeatherLocation).filter(
        WeatherLocation.id == location_id,
        WeatherLocation.user_id == current_user.id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Clear other primaries
    db.query(WeatherLocation).filter(
        WeatherLocation.user_id == current_user.id
    ).update({"is_primary": False})

    location.is_primary = True
    db.commit()
    db.refresh(location)

    return location


@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    location_id: Optional[int] = None,
    units: str = "fahrenheit",
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current weather for a location."""

    if location_id:
        location = db.query(WeatherLocation).filter(
            WeatherLocation.id == location_id,
            WeatherLocation.user_id == current_user.id
        ).first()
    else:
        # Get primary location
        location = db.query(WeatherLocation).filter(
            WeatherLocation.user_id == current_user.id,
            WeatherLocation.is_primary == True
        ).first()

    if not location:
        raise HTTPException(
            status_code=404, 
            detail="No location found. Please add a location first."
        )

    weather = await weather_service.get_weather_for_location(
        db, location, units, force_refresh=refresh
    )

    return {
        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude
        },
        **weather
    }


@router.get("/search", response_model=List[LocationSearchResult])
async def search_locations(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Search for locations by name."""
    if len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters"
        )

    results = await weather_service.search_locations(q)
    return results
```

### 4. Pydantic Schemas

#### backend/app/schemas/weather.py:
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class WeatherLocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: Optional[str] = "auto"
    is_primary: bool = False


class WeatherLocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_primary: Optional[bool] = None


class WeatherLocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    timezone: str
    is_primary: bool

    class Config:
        from_attributes = True


class CurrentWeather(BaseModel):
    temperature: int
    feels_like: int
    humidity: int
    wind_speed: int
    wind_direction: int
    precipitation: float
    weather_code: int
    description: str
    icon: str
    units: str


class DailyForecast(BaseModel):
    date: str
    temp_max: Optional[int]
    temp_min: Optional[int]
    precipitation: float
    precipitation_probability: int
    weather_code: int
    description: str
    icon: str
    sunrise: Optional[str]
    sunset: Optional[str]


class HourlyForecast(BaseModel):
    time: str
    temperature: Optional[int]
    precipitation_probability: int
    weather_code: int
    icon: str


class LocationSearchResult(BaseModel):
    name: str
    admin1: Optional[str]
    country: Optional[str]
    latitude: float
    longitude: float
    timezone: Optional[str]
    display_name: str


class WeatherResponse(BaseModel):
    location: WeatherLocationResponse
    current: CurrentWeather
    daily: List[DailyForecast]
    hourly: List[HourlyForecast]
    cached: bool
    cached_at: Optional[str] = None
    fetched_at: Optional[str] = None
```

### 5. Frontend Widget Component

#### frontend/src/components/widgets/WeatherWidget.jsx:
```jsx
import React, { useState, useEffect } from 'react';
import { 
  MapPin, RefreshCw, Plus, Settings, 
  Droplets, Wind, Thermometer, Sun, Moon
} from 'lucide-react';
import { useWeather } from '../../hooks/useWeather';

export default function WeatherWidget({ config }) {
  const { 
    weather, 
    locations, 
    loading, 
    error,
    refreshWeather,
    addLocation,
    searchLocations
  } = useWeather();

  const [showSettings, setShowSettings] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [units, setUnits] = useState(config?.units || 'fahrenheit');

  const handleSearch = async (query) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    const results = await searchLocations(query);
    setSearchResults(results);
  };

  const handleAddLocation = async (location) => {
    await addLocation({
      name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
      timezone: location.timezone
    });
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const getDayName = (dateStr, index) => {
    if (index === 0) return 'Today';
    if (index === 1) return 'Tomorrow';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  };

  if (loading && !weather) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!weather && locations.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-4">
        <MapPin className="w-12 h-12 text-gray-300 mb-3" />
        <p className="text-gray-500 mb-3">No location set</p>
        <button
          onClick={() => setShowSearch(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
        >
          Add Location
        </button>

        {showSearch && (
          <LocationSearchModal
            onSearch={handleSearch}
            results={searchResults}
            onSelect={handleAddLocation}
            onClose={() => setShowSearch(false)}
          />
        )}
      </div>
    );
  }

  const current = weather?.current;
  const daily = weather?.daily || [];
  const hourly = weather?.hourly || [];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-gray-500" />
          <span className="font-medium">{weather?.location?.name}</span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => refreshWeather(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Current Weather */}
      {current && (
        <div className="flex items-center gap-4 mb-4">
          <div className="text-5xl">{current.icon}</div>
          <div>
            <div className="text-4xl font-light">
              {current.temperature}°{units === 'fahrenheit' ? 'F' : 'C'}
            </div>
            <div className="text-gray-500">{current.description}</div>
          </div>
        </div>
      )}

      {/* Current Details */}
      {current && (
        <div className="grid grid-cols-3 gap-2 mb-4 text-sm">
          <div className="flex items-center gap-1 text-gray-600">
            <Thermometer className="w-4 h-4" />
            <span>Feels {current.feels_like}°</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <Droplets className="w-4 h-4" />
            <span>{current.humidity}%</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <Wind className="w-4 h-4" />
            <span>{current.wind_speed} mph</span>
          </div>
        </div>
      )}

      {/* Hourly Forecast */}
      {hourly.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs text-gray-500 uppercase mb-2">Hourly</h4>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {hourly.slice(0, 8).map((hour, idx) => (
              <div key={idx} className="flex flex-col items-center min-w-[50px]">
                <span className="text-xs text-gray-500">
                  {formatTime(hour.time)}
                </span>
                <span className="text-lg">{hour.icon}</span>
                <span className="text-sm font-medium">{hour.temperature}°</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7-Day Forecast */}
      {daily.length > 0 && (
        <div className="flex-1 overflow-y-auto">
          <h4 className="text-xs text-gray-500 uppercase mb-2">7-Day Forecast</h4>
          <div className="space-y-2">
            {daily.map((day, idx) => (
              <div key={idx} className="flex items-center justify-between py-1">
                <span className="w-20 text-sm">{getDayName(day.date, idx)}</span>
                <span className="text-lg">{day.icon}</span>
                <div className="flex items-center gap-2">
                  {day.precipitation_probability > 0 && (
                    <span className="text-xs text-blue-500">
                      {day.precipitation_probability}%
                    </span>
                  )}
                  <span className="text-sm font-medium w-8 text-right">
                    {day.temp_max}°
                  </span>
                  <span className="text-sm text-gray-400 w-8">
                    {day.temp_min}°
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sunrise/Sunset */}
      {daily[0] && (
        <div className="flex justify-center gap-6 mt-3 pt-3 border-t text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Sun className="w-3 h-3" />
            <span>{formatTime(daily[0].sunrise)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Moon className="w-3 h-3" />
            <span>{formatTime(daily[0].sunset)}</span>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <WeatherSettingsModal
          locations={locations}
          units={units}
          onUnitsChange={setUnits}
          onAddLocation={() => {
            setShowSettings(false);
            setShowSearch(true);
          }}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Search Modal */}
      {showSearch && (
        <LocationSearchModal
          onSearch={handleSearch}
          results={searchResults}
          onSelect={handleAddLocation}
          onClose={() => {
            setShowSearch(false);
            setSearchResults([]);
          }}
        />
      )}
    </div>
  );
}

function LocationSearchModal({ onSearch, results, onSelect, onClose }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Add Location</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <input
          type="text"
          placeholder="Search city..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-3 border rounded-lg mb-3"
          autoFocus
        />

        <div className="max-h-64 overflow-y-auto">
          {results.map((result, idx) => (
            <button
              key={idx}
              onClick={() => onSelect(result)}
              className="w-full text-left p-3 hover:bg-gray-50 rounded-lg"
            >
              <div className="font-medium">{result.name}</div>
              <div className="text-sm text-gray-500">
                {result.admin1}, {result.country}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function WeatherSettingsModal({ locations, units, onUnitsChange, onAddLocation, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-4 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold">Weather Settings</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        {/* Units Toggle */}
        <div className="mb-4">
          <label className="text-sm text-gray-500 block mb-2">Temperature Units</label>
          <div className="flex gap-2">
            <button
              onClick={() => onUnitsChange('fahrenheit')}
              className={`flex-1 py-2 rounded ${
                units === 'fahrenheit' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100'
              }`}
            >
              °F
            </button>
            <button
              onClick={() => onUnitsChange('celsius')}
              className={`flex-1 py-2 rounded ${
                units === 'celsius' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100'
              }`}
            >
              °C
            </button>
          </div>
        </div>

        {/* Locations */}
        <div className="mb-4">
          <label className="text-sm text-gray-500 block mb-2">Locations</label>
          <div className="space-y-2">
            {locations.map((loc) => (
              <div key={loc.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span>{loc.name}</span>
                {loc.is_primary && (
                  <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                    Primary
                  </span>
                )}
              </div>
            ))}
          </div>

          {locations.length < 5 && (
            <button
              onClick={onAddLocation}
              className="w-full mt-2 p-2 border-2 border-dashed rounded-lg text-gray-500 hover:border-blue-500 hover:text-blue-500"
            >
              + Add Location
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 6. React Hook

#### frontend/src/hooks/useWeather.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useWeather() {
  const [weather, setWeather] = useState(null);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLocations = useCallback(async () => {
    try {
      const response = await api.get('/weather/locations');
      setLocations(response.data);
      return response.data;
    } catch (err) {
      setError(err.message);
      return [];
    }
  }, []);

  const fetchWeather = useCallback(async (locationId = null, forceRefresh = false) => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (locationId) params.append('location_id', locationId);
      if (forceRefresh) params.append('refresh', 'true');

      const response = await api.get(`/weather/current?${params}`);
      setWeather(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status !== 404) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const locs = await fetchLocations();
      if (locs.length > 0) {
        await fetchWeather();
      } else {
        setLoading(false);
      }
    };
    init();
  }, [fetchLocations, fetchWeather]);

  const refreshWeather = (forceRefresh = false) => {
    return fetchWeather(null, forceRefresh);
  };

  const addLocation = async (locationData) => {
    try {
      const response = await api.post('/weather/locations', locationData);
      setLocations(prev => [...prev, response.data]);
      await fetchWeather(response.data.id);
      return response.data;
    } catch (err) {
      throw err;
    }
  };

  const searchLocations = async (query) => {
    try {
      const response = await api.get(`/weather/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (err) {
      return [];
    }
  };

  return {
    weather,
    locations,
    loading,
    error,
    refreshWeather,
    addLocation,
    searchLocations,
    fetchWeather
  };
}
```

## Unit Tests

### tests/test_weather_service.py:
```python
import pytest
from unittest.mock import patch, AsyncMock
from app.services.weather_service import OpenMeteoService, WeatherService

@pytest.mark.asyncio
async def test_weather_code_mapping():
    service = OpenMeteoService()

    # Test known codes
    assert service.WEATHER_CODES[0] == ("Clear sky", "☀️")
    assert service.WEATHER_CODES[95] == ("Thunderstorm", "⛈️")
    assert service.WEATHER_CODES[71] == ("Slight snow", "❄️")

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_search_location(mock_get):
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "New York",
                "admin1": "New York",
                "country": "United States",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York"
            }
        ]
    }
    mock_response.raise_for_status = lambda: None
    mock_get.return_value = mock_response

    service = OpenMeteoService()
    results = await service.search_location("New York")

    assert len(results) == 1
    assert results[0]["name"] == "New York"
    assert results[0]["latitude"] == 40.7128

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_get_weather(mock_get):
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 72.5,
            "relative_humidity_2m": 65,
            "apparent_temperature": 75.0,
            "weather_code": 1,
            "wind_speed_10m": 10.5,
            "wind_direction_10m": 180,
            "precipitation": 0
        },
        "daily": {
            "time": ["2024-01-01"],
            "weather_code": [1],
            "temperature_2m_max": [75],
            "temperature_2m_min": [55],
            "precipitation_sum": [0],
            "precipitation_probability_max": [10],
            "sunrise": ["2024-01-01T07:00"],
            "sunset": ["2024-01-01T17:30"]
        },
        "hourly": {
            "time": ["2024-01-01T12:00"],
            "temperature_2m": [72],
            "weather_code": [1],
            "precipitation_probability": [5]
        },
        "timezone": "America/New_York"
    }
    mock_response.raise_for_status = lambda: None
    mock_get.return_value = mock_response

    service = OpenMeteoService()
    weather = await service.get_weather(40.7128, -74.0060)

    assert weather["current"]["temperature"] == 73  # Rounded
    assert weather["current"]["description"] == "Mainly clear"
    assert len(weather["daily"]) == 1
    assert len(weather["hourly"]) == 1
```

## Acceptance Criteria
- [ ] Weather displays current conditions with icon
- [ ] 7-day forecast shows daily high/low
- [ ] Hourly forecast shows next 8 hours
- [ ] Location search works
- [ ] Multiple locations can be saved (max 5)
- [ ] Primary location is shown by default
- [ ] Temperature units can be toggled (°F/°C)
- [ ] Weather data is cached for 30 minutes
- [ ] Manual refresh bypasses cache
- [ ] Sunrise/sunset times displayed
- [ ] Unit tests pass

## Notes
- Open-Meteo is completely free with no API key
- Consider adding weather alerts in future iteration
- Cache duration can be adjusted based on usage

## Estimated Time
2-3 hours

## Next Task
Task 013: Stock & Crypto Widgets
