import { useState, useEffect, useRef } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../../services/api';

const WEATHER_ICONS = {
  sunny: '☀️',
  partly_cloudy: '⛅',
  cloudy: '☁️',
  rainy: '🌧️',
  snowy: '❄️',
  stormy: '⛈️',
};

function WeatherIcon({ icon, size = 'large' }) {
  const emoji = WEATHER_ICONS[icon] || '☁️';
  const sizeClass = size === 'large' ? 'text-5xl' : size === 'small' ? 'text-lg' : 'text-sm';
  return <span className={sizeClass}>{emoji}</span>;
}

function SunTimes({ sunTimes }) {
  if (!sunTimes) return null;

  // Calculate progress through the day (0-100%)
  const now = Date.now() / 1000; // Current time in seconds
  const sunriseTime = sunTimes.sunrise_timestamp;
  const sunsetTime = sunTimes.sunset_timestamp;

  let progress = 0;
  let isDay = false;

  if (now < sunriseTime) {
    // Before sunrise - show 0% (night)
    progress = 0;
    isDay = false;
  } else if (now >= sunriseTime && now <= sunsetTime) {
    // Between sunrise and sunset - calculate progress
    const dayLength = sunsetTime - sunriseTime;
    const elapsed = now - sunriseTime;
    progress = (elapsed / dayLength) * 100;
    isDay = true;
  } else {
    // After sunset - show 100% (night)
    progress = 100;
    isDay = false;
  }

  return (
    <div className="px-2 py-2 border-t border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-center text-xs mb-2">
        <div className="flex items-center gap-1">
          <span>🌅</span>
          <span className="text-gray-700 dark:text-gray-300">{sunTimes.sunrise}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🌆</span>
          <span className="text-gray-700 dark:text-gray-300">{sunTimes.sunset}</span>
        </div>
      </div>
      {/* Progress bar */}
      <div className="relative h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full transition-all duration-500 ${
            isDay
              ? 'bg-gradient-to-r from-orange-400 via-yellow-300 to-orange-400'
              : 'bg-gray-400 dark:bg-gray-600'
          }`}
          style={{ width: `${progress}%` }}
        />
        {/* Sun indicator */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-yellow-400 border-2 border-white dark:border-gray-800 shadow-lg transition-all duration-500"
          style={{ left: `calc(${progress}% - 6px)` }}
        />
      </div>
    </div>
  );
}

function CurrentConditions({ current, units }) {
  const tempUnit = units === 'metric' ? '°C' : '°F';

  return (
    <div className="text-center py-1">
      <WeatherIcon icon={current.icon} size="large" />
      <div className="text-3xl font-bold text-gray-800 dark:text-gray-100 mt-1">
        {current.temp !== null ? `${Math.round(current.temp)}${tempUnit}` : '—'}
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {current.description || 'Unknown'}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
        {current.feels_like !== null && (
          <span>Feels like {Math.round(current.feels_like)}°</span>
        )}
        {current.feels_like !== null && current.humidity !== null && ' • '}
        {current.humidity !== null && (
          <span>Humidity {current.humidity}%</span>
        )}
      </div>
    </div>
  );
}

function HourlyForecast({ hourly, units, externalUrl }) {
  if (!hourly || hourly.length === 0) return null;

  return (
    <div className="flex gap-2 overflow-x-auto py-2 px-1 scrollbar-thin">
      {hourly.map((hour, index) => {
        const isMidnight = hour.time === "12 AM";
        return (
          <a
            key={index}
            href={externalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex flex-col items-center min-w-[3rem] text-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded p-1 transition-colors cursor-pointer ${
              isMidnight ? 'border-l-2 border-gray-300 dark:border-gray-600 pl-2 ml-1' : ''
            }`}
            title="View detailed forecast"
          >
            <span className="text-xs text-gray-500 dark:text-gray-400">{hour.time}</span>
            <WeatherIcon icon={hour.icon} size="tiny" />
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
              {hour.temp !== null ? `${Math.round(hour.temp)}°` : '—'}
            </span>
            {hour.precip_chance !== null && hour.precip_chance > 0 && (
              <span className="text-xs text-blue-500">
                {hour.precip_chance}%
              </span>
            )}
          </a>
        );
      })}
    </div>
  );
}

function Forecast({ forecast, selectedDate, onSelectDate }) {
  return (
    <div className="flex justify-between border-t border-gray-200 dark:border-gray-700 pt-2">
      {forecast.map((day, index) => {
        const isSelected = selectedDate === day.date;
        return (
          <button
            key={index}
            onClick={() => onSelectDate(isSelected ? null : day.date)}
            className={`flex flex-col items-center flex-1 py-1 rounded transition-colors ${
              isSelected
                ? 'bg-blue-100 dark:bg-blue-900/30'
                : 'hover:bg-gray-100 dark:hover:bg-gray-700/50'
            }`}
          >
            <span className={`text-xs ${isSelected ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-500 dark:text-gray-400'}`}>
              {day.day}
            </span>
            <WeatherIcon icon={day.icon} size="small" />
            <div className="text-xs text-gray-700 dark:text-gray-300">
              {day.high !== null ? Math.round(day.high) : '—'}
              <span className="text-gray-400 dark:text-gray-500">
                /{day.low !== null ? Math.round(day.low) : '—'}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

// Leaflet radar overlay component
function RadarOverlay({ frames, host, currentFrameIndex }) {
  const map = useMap();
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!frames || frames.length === 0 || currentFrameIndex < 0) return;

    const frame = frames[currentFrameIndex];
    if (!frame) return;

    // Remove old overlay if exists
    if (overlayRef.current) {
      map.removeLayer(overlayRef.current);
    }

    // Create new tile layer for current frame
    const tileUrl = `${host}${frame.path}/256/{z}/{x}/{y}/2/1_1.png`;

    // Import L from leaflet
    import('leaflet').then(({ default: L }) => {
      overlayRef.current = L.tileLayer(tileUrl, {
        opacity: 0.6,
        zIndex: 1000,
      }).addTo(map);
    });

    return () => {
      if (overlayRef.current) {
        map.removeLayer(overlayRef.current);
      }
    };
  }, [frames, host, currentFrameIndex, map]);

  return null;
}

function WeatherRadar({ location }) {
  const [expanded, setExpanded] = useState(false);
  const [radarData, setRadarData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const animationRef = useRef(null);

  // Parse location coordinates
  const coords = location?.split(',').map(c => parseFloat(c.trim()));
  const [lat, lon] = coords && coords.length === 2 && !isNaN(coords[0]) && !isNaN(coords[1])
    ? coords
    : [42.3601, -71.0589]; // Default to Boston if coordinates are invalid

  // Fetch radar data when expanded
  useEffect(() => {
    if (expanded && !radarData && !loading) {
      setLoading(true);
      api.get('/weather/radar')
        .then(response => {
          setRadarData(response.data);
          setError(null);
        })
        .catch(err => {
          setError('Failed to load radar data');
          console.error('Radar error:', err);
        })
        .finally(() => setLoading(false));
    }
  }, [expanded, radarData, loading]);

  // Animation loop
  useEffect(() => {
    if (isPlaying && radarData?.frames?.length > 0) {
      animationRef.current = setInterval(() => {
        setCurrentFrameIndex(prev => (prev + 1) % radarData.frames.length);
      }, 500); // Change frame every 500ms
    } else if (animationRef.current) {
      clearInterval(animationRef.current);
    }

    return () => {
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
    };
  }, [isPlaying, radarData]);

  if (!expanded) {
    return (
      <div className="border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setExpanded(true)}
          className="w-full px-2 py-2 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
        >
          <span>🌧️ Show Weather Radar</span>
          <span>▼</span>
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700">
      <div className="px-2 py-2">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Weather Radar</span>
          <button
            onClick={() => setExpanded(false)}
            className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ▲ Hide
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-48 bg-gray-100 dark:bg-gray-700 rounded">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-48 bg-gray-100 dark:bg-gray-700 rounded text-xs text-red-500">
            {error}
          </div>
        )}

        {!loading && !error && radarData && (
          <>
            <div className="h-48 rounded overflow-hidden border border-gray-300 dark:border-gray-600 mb-2">
              <MapContainer
                center={[lat, lon]}
                zoom={8}
                style={{ height: '100%', width: '100%' }}
                zoomControl={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                <RadarOverlay
                  frames={radarData.frames}
                  host={radarData.host}
                  currentFrameIndex={currentFrameIndex}
                />
              </MapContainer>
            </div>

            {/* Animation controls */}
            <div className="flex items-center justify-between text-xs">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                {isPlaying ? '⏸ Pause' : '▶ Play'}
              </button>
              <span className="text-gray-600 dark:text-gray-400">
                {radarData.frames.length} frames • {Math.round(radarData.frames.length * 0.5 / 60)} min
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function SelectedDayHourly({ forecast, selectedDate, units, externalUrl }) {
  const selectedDay = forecast.find((d) => d.date === selectedDate);
  if (!selectedDay || !selectedDay.hourly || selectedDay.hourly.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 mt-2 pt-2">
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
        {selectedDay.day} Hourly
      </div>
      <HourlyForecast hourly={selectedDay.hourly} units={units} externalUrl={externalUrl} />
    </div>
  );
}

export default function WeatherWidget({ config }) {
  const [selectedDate, setSelectedDate] = useState(null);

  const { data, loading, error } = useWidgetData({
    endpoint: '/weather',
    params: {
      location: config.location,
      units: config.units || 'imperial',
      provider: config.api_provider || 'openmeteo',
      api_key: config.api_key || undefined,
      external_forecast_provider: config.external_forecast_provider || 'windy',
    },
    refreshInterval: config.refresh_interval || 900,
    enabled: !!config.location,
  });

  if (!config.location) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <span className="text-4xl mb-2">🌤️</span>
        <p className="text-sm">No location set</p>
        <p className="text-xs mt-1">Open settings to add a location</p>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500">
        <p className="text-sm text-center">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Prefer saved display name over API-returned location
  const displayLocation = config.location_display || data.location;
  const units = config.units || 'imperial';

  return (
    <div className="flex flex-col">
      <div className="text-xs text-gray-500 dark:text-gray-400 text-right mb-1">
        {displayLocation}
      </div>

      <div className="flex-shrink-0">
        <CurrentConditions current={data.current} units={units} />
      </div>

      {/* Sunrise/Sunset times with progression bar */}
      {data.sun_times && (
        <div className="flex-shrink-0">
          <SunTimes sunTimes={data.sun_times} />
        </div>
      )}

      {/* Today's hourly forecast (default view when no day selected) */}
      {!selectedDate && data.today_hourly && data.today_hourly.length > 0 && (
        <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 mt-1 pt-1">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Today</div>
          <HourlyForecast hourly={data.today_hourly} units={units} externalUrl={data.external_forecast_url} />
        </div>
      )}

      {/* Selected day's hourly forecast */}
      {selectedDate && (
        <div className="flex-shrink-0 overflow-hidden">
          <SelectedDayHourly forecast={data.forecast} selectedDate={selectedDate} units={units} externalUrl={data.external_forecast_url} />
        </div>
      )}

      {/* Weather Radar - expandable */}
      {config.show_radar !== false && (
        <div className="flex-shrink-0">
          <WeatherRadar location={config.location} />
        </div>
      )}

      {/* 5-day forecast - always at bottom */}
      {data.forecast && data.forecast.length > 0 && (
        <div className="mt-auto flex-shrink-0">
          <Forecast
            forecast={data.forecast}
            selectedDate={selectedDate}
            onSelectDate={setSelectedDate}
          />
        </div>
      )}
    </div>
  );
}
