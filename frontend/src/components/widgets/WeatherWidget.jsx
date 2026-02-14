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

  const now = Date.now() / 1000; // Current time in seconds
  const sunriseTime = sunTimes.sunrise_timestamp;
  const sunsetTime = sunTimes.sunset_timestamp;

  // Determine if we're in day mode (between sunrise and sunset) or night mode
  const isDay = now >= sunriseTime && now < sunsetTime;

  let progress = 0;
  let timeUntilTransition = "";
  let indicatorEmoji = "";
  let gradientClass = "";

  if (isDay) {
    // DAY MODE: Show sun progress from sunrise to sunset
    const dayLength = sunsetTime - sunriseTime;
    const elapsed = now - sunriseTime;
    progress = Math.min(100, (elapsed / dayLength) * 100);

    // Calculate time until sunset
    const secondsUntilSunset = sunsetTime - now;
    timeUntilTransition = formatTimeRemaining(secondsUntilSunset, "sunset");

    indicatorEmoji = "☀️";
    gradientClass = "bg-gradient-to-r from-orange-400 via-yellow-300 to-orange-400";
  } else {
    // NIGHT MODE: Show moon progress from sunset to next sunrise
    // Calculate next sunrise (either today if before sunrise, or tomorrow if after sunset)
    const nextSunrise = now < sunriseTime ? sunriseTime : sunriseTime + 86400; // Add 24 hours

    // Night period is from sunset to next sunrise
    let nightStart = now < sunriseTime ? sunsetTime - 86400 : sunsetTime; // Yesterday's or today's sunset
    const nightLength = nextSunrise - nightStart;
    const elapsed = now - nightStart;
    progress = Math.min(100, (elapsed / nightLength) * 100);

    // Calculate time until sunrise
    const secondsUntilSunrise = nextSunrise - now;
    timeUntilTransition = formatTimeRemaining(secondsUntilSunrise, "sunrise");

    indicatorEmoji = "🌙";
    gradientClass = "bg-gradient-to-r from-indigo-600 via-purple-500 to-indigo-600";
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

      {/* Time until next transition */}
      <div className="text-xs text-center text-gray-500 dark:text-gray-400 mb-1">
        {timeUntilTransition}
      </div>

      {/* Smart Day/Night Progress bar */}
      <div className="relative h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full transition-all duration-500 ${gradientClass}`}
          style={{ width: `${progress}%` }}
        />
        {/* Sun/Moon indicator */}
        <div
          className="absolute top-1/2 -translate-y-1/2 transition-all duration-500 flex items-center justify-center"
          style={{ left: `calc(${progress}% - 8px)` }}
        >
          <span className="text-sm drop-shadow-lg">{indicatorEmoji}</span>
        </div>
      </div>
    </div>
  );
}

// Helper function to format time remaining
function formatTimeRemaining(seconds, eventName) {
  if (seconds <= 0) return "";

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m until ${eventName}`;
  } else {
    return `${minutes}m until ${eventName}`;
  }
}

function MoonPhase({ moonPhase }) {
  if (!moonPhase) return null;

  return (
    <div className="px-2 py-2 border-t border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{moonPhase.phase_emoji}</span>
          <div className="flex flex-col">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
              {moonPhase.phase_name}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {moonPhase.illumination}% illuminated
            </span>
          </div>
        </div>
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

// Alerts overlay component for radar map
function AlertsOverlay({ alerts }) {
  const map = useMap();
  const alertLayersRef = useRef([]);

  useEffect(() => {
    if (!alerts || alerts.length === 0) {
      // Clear existing alert layers
      alertLayersRef.current.forEach(layer => map.removeLayer(layer));
      alertLayersRef.current = [];
      return;
    }

    // Import Leaflet dynamically
    import('leaflet').then(({ default: L }) => {
      // Clear old layers
      alertLayersRef.current.forEach(layer => map.removeLayer(layer));
      alertLayersRef.current = [];

      // Add each alert polygon
      alerts.forEach(alert => {
        if (!alert.geometry) return;

        // Determine color by severity
        const colors = {
          'Extreme': { color: '#DC2626', fillColor: '#FCA5A5', fillOpacity: 0.3 },
          'Severe': { color: '#EA580C', fillColor: '#FDBA74', fillOpacity: 0.25 },
          'Moderate': { color: '#EAB308', fillColor: '#FDE047', fillOpacity: 0.2 },
          'Minor': { color: '#3B82F6', fillColor: '#93C5FD', fillOpacity: 0.15 },
        };

        const style = colors[alert.severity] || colors['Minor'];

        // Create GeoJSON layer
        const layer = L.geoJSON(alert.geometry, {
          style: {
            color: style.color,
            weight: 2,
            fillColor: style.fillColor,
            fillOpacity: style.fillOpacity,
          }
        }).addTo(map);

        // Add popup with alert details
        const popupContent = `
          <div style="max-width: 300px;">
            <strong style="color: ${style.color};">${alert.event}</strong><br/>
            <em>${alert.headline}</em><br/>
            <small>${alert.affected_areas}</small>
          </div>
        `;
        layer.bindPopup(popupContent);

        alertLayersRef.current.push(layer);
      });
    });

    return () => {
      alertLayersRef.current.forEach(layer => map.removeLayer(layer));
      alertLayersRef.current = [];
    };
  }, [alerts, map]);

  return null;
}

function WeatherRadar({ location }) {
  const [expanded, setExpanded] = useState(false);
  const [radarData, setRadarData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [alertsData, setAlertsData] = useState(null);
  const [showAlerts, setShowAlerts] = useState(true);
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

  // Fetch alerts when expanded
  useEffect(() => {
    if (expanded && !alertsData && location) {
      api.get('/weather/alerts', {
        params: { location }
      })
        .then(response => {
          setAlertsData(response.data);
        })
        .catch(err => {
          console.error('Failed to load weather alerts:', err);
          setAlertsData({ alerts: [], alert_count: 0 });
        });
    }
  }, [expanded, location, alertsData]);

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
                {showAlerts && alertsData && alertsData.alerts && (
                  <AlertsOverlay alerts={alertsData.alerts} />
                )}
              </MapContainer>
            </div>

            {/* Animation controls */}
            <div className="flex items-center justify-between text-xs mb-2">
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

            {/* Alert toggle button */}
            {alertsData && alertsData.alert_count > 0 && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">
                  {alertsData.alert_count} active alert{alertsData.alert_count !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={() => setShowAlerts(!showAlerts)}
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                >
                  {showAlerts ? 'Hide' : 'Show'} Alerts
                </button>
              </div>
            )}
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

function WeatherAlertsList({ alerts }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 mt-2 pt-2">
      <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
        <span>⚠️</span>
        <span>Active Weather Alerts</span>
      </div>
      {alerts.map((alert, idx) => {
        const severityColors = {
          'Extreme': 'text-red-600 dark:text-red-400',
          'Severe': 'text-orange-600 dark:text-orange-400',
          'Moderate': 'text-yellow-600 dark:text-yellow-400',
          'Minor': 'text-blue-600 dark:text-blue-400',
        };
        const colorClass = severityColors[alert.severity] || severityColors['Minor'];

        return (
          <div key={idx} className="mb-2 text-xs">
            <div className={`font-medium ${colorClass}`}>{alert.event}</div>
            <div className="text-gray-600 dark:text-gray-400">{alert.headline}</div>
            <div className="text-gray-500 dark:text-gray-500 text-xs">
              Until {new Date(alert.expires).toLocaleString()}
            </div>
          </div>
        );
      })}
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

  // Fetch alerts independently (separate from radar)
  const { data: alertsData } = useWidgetData({
    endpoint: '/weather/alerts',
    params: { location: config.location },
    refreshInterval: 300,  // 5 minutes
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

      {/* Moon phase */}
      {data.moon_phase && (
        <div className="flex-shrink-0">
          <MoonPhase moonPhase={data.moon_phase} />
        </div>
      )}

      {/* Active weather alerts */}
      {alertsData && alertsData.alert_count > 0 && (
        <div className="flex-shrink-0">
          <WeatherAlertsList alerts={alertsData.alerts} />
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
