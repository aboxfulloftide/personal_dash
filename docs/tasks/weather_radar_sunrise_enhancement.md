# Weather Widget Enhancement: Radar & Sun Times

## Overview
Add weather radar map and sunrise/sunset times to the existing weather widget to provide more comprehensive weather information.

## Current State
- Weather widget shows current conditions, hourly forecast, and 5-day forecast
- Uses Open-Meteo API for weather data
- Located at:
  - Backend: `backend/app/api/v1/endpoints/weather.py`
  - Frontend: `frontend/src/components/widgets/WeatherWidget.jsx`

## Proposed Features

### 1. Weather Radar Map
**Display animated weather radar showing precipitation**

#### Data Source Options:
- **RainViewer API** (Recommended)
  - Free, no API key required
  - Provides animated radar tiles
  - Global coverage
  - URL: `https://api.rainviewer.com/public/weather-maps.json`
  - Returns timestamp URLs for radar tiles

- **Alternative: NOAA/NWS** (US only)
  - Free for US locations
  - Ridge radar images
  - More detailed but US-specific

#### Implementation Plan:
1. **Backend Changes:**
   - Add new endpoint `/weather/radar` that returns RainViewer tile URLs
   - Input: lat/lon coordinates
   - Output: Array of radar tile URLs with timestamps

2. **Frontend Changes:**
   - Add new "Radar" tab/view toggle in weather widget
   - Use Leaflet.js or simple img overlay for radar display
   - Show animated radar loop (last 30-60 minutes)
   - Center map on user's location with zoom controls
   - Show timestamp of radar image

3. **Widget Settings:**
   - Toggle to enable/disable radar (default: enabled)
   - Radar refresh interval (default: 5 minutes)
   - Map zoom level preference

### 2. Sunrise/Sunset Times
**Display daily sun position data**

#### Data Source:
- **Open-Meteo API** (Already used)
  - Sunrise/sunset times included in API response
  - Add `&daily=sunrise,sunset` parameter
  - Also provides: UV index, daylight duration

- **Sunrise Equation** (Fallback)
  - Calculate locally using lat/lon if API unavailable
  - Less accurate but no API dependency

#### Implementation Plan:
1. **Backend Changes:**
   - Update `WeatherResponse` schema to include sun times:
     ```python
     sunrise: str  # "6:45 AM"
     sunset: str   # "5:32 PM"
     daylight_duration: str  # "10h 47m"
     ```
   - Parse Open-Meteo sunrise/sunset from daily data
   - Convert UTC times to local timezone
   - Calculate daylight duration

2. **Frontend Changes:**
   - Add sun times display below current conditions:
     ```
     🌅 6:45 AM    🌆 5:32 PM    ☀️ 10h 47m
     ```
   - Use sunrise/sunset emoji icons
   - Show relative time (e.g., "Sunset in 2h 15m")
   - Add visual indicator bar showing day/night progression

3. **Widget Settings:**
   - Toggle to show/hide sun times (default: shown)
   - Show relative times vs absolute times

### 3. Extended Hourly Forecast
**Show hourly forecast every 2 hours through midnight**

#### Current State:
- Hourly forecast currently shows ~6-8 hours ahead
- Stops around 10 PM

#### Improvements:
1. **Backend Changes:**
   - Extend hourly forecast to show every 2 hours until midnight
   - Example: If current time is 3 PM, show: 4 PM, 6 PM, 8 PM, 10 PM, 12 AM
   - Request more hourly data from Open-Meteo API (currently limited)
   - Parse up to 12-16 hours ahead

2. **Frontend Changes:**
   - Display hourly forecast in 2-hour intervals through midnight
   - Horizontal scroll for all hours
   - Show midnight as "12 AM" (end of day indicator)
   - Add visual separator or indicator at midnight

3. **Clickable Hourly Items:**
   - Make each hourly forecast item clickable
   - Opens new tab with detailed forecast
   - Link to external weather service

#### External Weather Service Options:
**Do NOT use weather.com** (per requirements)

**Option A: Weather Underground (Recommended)**
- URL format: `https://www.wunderground.com/forecast/us/[state]/[city]`
- Example: `https://www.wunderground.com/forecast/us/mi/trenton`
- Need to format location from lat/lon or location name
- Pros: Detailed hourly, good UI, community-based
- Cons: Need to construct URL from location data

**Option B: OpenWeather (openweathermap.org)**
- URL format: `https://openweathermap.org/city/[city_id]`
- Example: `https://openweathermap.org/city/5019767` (Detroit)
- Need to map location to city ID
- Pros: Clean interface, free
- Cons: Need city ID lookup

**Option C: Windy.com**
- URL format: `https://www.windy.com/[lat]/[lon]`
- Example: `https://www.windy.com/42.1292/-83.1913`
- Direct lat/lon support (easiest!)
- Pros: Detailed maps, no lookup needed
- Cons: More map-focused than forecast-focused

**Option D: National Weather Service (US only)**
- URL format: `https://forecast.weather.gov/MapClick.php?lat=[lat]&lon=[lon]`
- Example: `https://forecast.weather.gov/MapClick.php?lat=42.1292&lon=-83.1913`
- Direct lat/lon support
- Pros: Official US government source, very detailed
- Cons: US only, less polished UI

**Recommendation: Weather Underground** for best forecast details, fallback to **Windy.com** for simplicity (no location parsing needed)

#### Implementation:
```python
# Backend - Add to WeatherResponse
external_forecast_url: str  # Pre-built URL for external site

# In weather endpoint
def get_external_forecast_url(lat: float, lon: float, location_name: str) -> str:
    """Generate URL for external weather forecast"""
    # Option 1: Weather Underground (need city/state)
    # Parse location_name or geocode to get city/state
    state = "mi"  # From geocoding
    city = "trenton"  # From location_name
    return f"https://www.wunderground.com/forecast/us/{state}/{city}"

    # Option 2: Windy (simplest - just lat/lon)
    return f"https://www.windy.com/{lat}/{lon}"

    # Option 3: NWS (US only)
    return f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}"
```

```javascript
// Frontend - Make hourly items clickable
<a
  href={externalForecastUrl}
  target="_blank"
  rel="noopener noreferrer"
  className="flex flex-col items-center min-w-[3rem] hover:bg-gray-100 dark:hover:bg-gray-700 rounded p-1 transition-colors cursor-pointer"
  title="View detailed forecast"
>
  <span className="text-xs text-gray-500">{hour.time}</span>
  <WeatherIcon icon={hour.icon} size="tiny" />
  <span className="text-xs font-medium">{hour.temp}°</span>
</a>
```

## UI/UX Design

### Layout Options:

**Option A: Tabbed View**
```
┌─────────────────────────────────┐
│ Current | Forecast | Radar      │
├─────────────────────────────────┤
│                                 │
│    [Radar Map Display]          │
│                                 │
└─────────────────────────────────┘
```

**Option B: Expandable Section**
```
┌─────────────────────────────────┐
│ Current Conditions + Sun Times  │
├─────────────────────────────────┤
│ Hourly Forecast                 │
├─────────────────────────────────┤
│ 5-Day Forecast                  │
├─────────────────────────────────┤
│ ▼ Radar Map (Click to expand)  │
└─────────────────────────────────┘
```

**Option C: Always Visible (Larger Widget)**
```
┌─────────────┬───────────────────┐
│  Current    │                   │
│  + Sun      │   Radar Map       │
│  Times      │                   │
├─────────────┴───────────────────┤
│        5-Day Forecast           │
└─────────────────────────────────┘
```

**Recommendation: Option B** - Expandable section
- Doesn't clutter the widget when not needed
- Easy to access when desired
- Maintains current compact design

## Technical Considerations

### Performance:
- Cache radar tiles for 5 minutes (they don't update faster)
- Lazy load radar component (only load when expanded)
- Optimize image loading with proper sizing

### Mobile/Responsive:
- Radar map should be touch-friendly with pinch-zoom
- Sun times should wrap gracefully on small widgets
- Consider simplified radar view on very small widgets

### Error Handling:
- Show placeholder if radar unavailable
- Fall back to text-only for sun times if calculation fails
- Display last successful radar timestamp

## Implementation Steps

### Phase 1: Extended Hourly Forecast (Quick Win)
1. Update backend to request more hourly data from Open-Meteo API
2. Filter/format to show every 2 hours through midnight
3. Add external forecast URL generation (Weather Underground or Windy)
4. Update frontend to display extended hourly with horizontal scroll
5. Make hourly items clickable (open external forecast in new tab)
6. Add midnight indicator/separator
7. Test with various times of day

### Phase 2: Sunrise/Sunset (Easier)
1. Update backend weather.py schema with sun times fields
2. Parse sunrise/sunset from Open-Meteo API response
3. Update frontend WeatherWidget to display sun times
4. Add time formatting utilities (relative time)
5. Add widget setting for sun times display
6. Test with various timezones

### Phase 3: Weather Radar (More Complex)
1. Research and test RainViewer API integration
2. Create backend `/weather/radar` endpoint
3. Add frontend radar component with map library
4. Implement expandable/collapsible radar section
5. Add animation controls (play/pause/speed)
6. Add widget settings for radar preferences
7. Test performance and optimize image loading

## Dependencies

### Frontend:
- **Leaflet.js** (~40KB) - For interactive radar map
  - Alternative: Mapbox GL JS (larger but more features)
  - Alternative: Simple img tag (no interactivity)

### Backend:
- No new dependencies (httpx already used)

## Future Enhancements
- Show lightning strikes on radar (if available)
- Add severe weather alerts overlay
- Show cloud cover prediction
- Golden hour times for photographers (sunrise + 1hr, sunset - 1hr)
- Moon phase display
- Air quality index overlay on radar

## Estimated Effort
- **Extended Hourly Forecast:** 1-2 hours
- **Sunrise/Sunset:** 2-3 hours
- **Weather Radar:** 4-6 hours
- **Total:** 7-11 hours

## Priority
**Medium-High** - Adds significant value to weather widget, relatively straightforward implementation. Extended hourly forecast is quickest win.
