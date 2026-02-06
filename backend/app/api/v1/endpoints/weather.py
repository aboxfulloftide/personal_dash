import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import CurrentActiveUser

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


class ForecastDay(BaseModel):
    day: str
    high: float | None
    low: float | None
    icon: str


class WeatherResponse(BaseModel):
    location: str
    current: CurrentWeather
    forecast: list[ForecastDay]


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


async def fetch_openmeteo(lat: float, lon: float, units: str) -> dict:
    """Fetch weather from Open-Meteo API."""
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
        f"&temperature_unit={temp_unit}"
        f"&timezone=auto"
        f"&forecast_days=5"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10.0)
        data = resp.json()

    current_data = data.get("current", {})
    daily_data = data.get("daily", {})

    weather_code = current_data.get("weather_code", 0)

    current = CurrentWeather(
        temp=current_data.get("temperature_2m"),
        feels_like=current_data.get("apparent_temperature"),
        humidity=current_data.get("relative_humidity_2m"),
        description=WMO_CODE_TO_DESC.get(weather_code, "Unknown"),
        icon=WMO_CODE_TO_ICON.get(weather_code, "cloudy"),
    )

    forecast = []
    times = daily_data.get("time", [])
    highs = daily_data.get("temperature_2m_max", [])
    lows = daily_data.get("temperature_2m_min", [])
    codes = daily_data.get("weather_code", [])

    for i, date_str in enumerate(times[:5]):
        date = datetime.strptime(date_str, "%Y-%m-%d")
        code = codes[i] if i < len(codes) else 0
        forecast.append(ForecastDay(
            day=date.strftime("%a"),
            high=highs[i] if i < len(highs) else None,
            low=lows[i] if i < len(lows) else None,
            icon=WMO_CODE_TO_ICON.get(code, "cloudy"),
        ))

    return {"current": current, "forecast": forecast}


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


@router.get("", response_model=WeatherResponse)
async def get_weather(
    current_user: CurrentActiveUser,
    location: str = Query(..., description="City name or location"),
    units: str = Query("imperial", description="imperial or metric"),
    provider: str = Query("openmeteo", description="API provider"),
    api_key: str | None = Query(None, description="API key for OpenWeatherMap"),
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

    return WeatherResponse(
        location=display_name,
        current=result["current"],
        forecast=result["forecast"],
    )
