import { useState } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';

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

function HourlyForecast({ hourly, units }) {
  if (!hourly || hourly.length === 0) return null;

  return (
    <div className="flex gap-2 overflow-x-auto py-2 px-1 scrollbar-thin">
      {hourly.map((hour, index) => (
        <div
          key={index}
          className="flex flex-col items-center min-w-[3rem] text-center"
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
        </div>
      ))}
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

function SelectedDayHourly({ forecast, selectedDate, units }) {
  const selectedDay = forecast.find((d) => d.date === selectedDate);
  if (!selectedDay || !selectedDay.hourly || selectedDay.hourly.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 mt-2 pt-2">
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
        {selectedDay.day} Hourly
      </div>
      <HourlyForecast hourly={selectedDay.hourly} units={units} />
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
    <div className="h-full flex flex-col overflow-hidden">
      <div className="text-xs text-gray-500 dark:text-gray-400 text-right mb-1">
        {displayLocation}
      </div>

      <div className="flex-shrink-0">
        <CurrentConditions current={data.current} units={units} />
      </div>

      {/* Today's hourly forecast (default view when no day selected) */}
      {!selectedDate && data.today_hourly && data.today_hourly.length > 0 && (
        <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 mt-1 pt-1">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Today</div>
          <HourlyForecast hourly={data.today_hourly} units={units} />
        </div>
      )}

      {/* Selected day's hourly forecast */}
      {selectedDate && (
        <div className="flex-shrink-0 overflow-hidden">
          <SelectedDayHourly forecast={data.forecast} selectedDate={selectedDate} units={units} />
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
