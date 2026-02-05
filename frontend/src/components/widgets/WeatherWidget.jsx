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
  const sizeClass = size === 'large' ? 'text-5xl' : 'text-xl';
  return <span className={sizeClass}>{emoji}</span>;
}

function CurrentConditions({ current, units }) {
  const tempUnit = units === 'metric' ? '°C' : '°F';

  return (
    <div className="text-center py-2">
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

function Forecast({ forecast, units }) {
  const tempUnit = units === 'metric' ? '°' : '°';

  return (
    <div className="flex justify-between border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
      {forecast.map((day, index) => (
        <div key={index} className="flex flex-col items-center flex-1">
          <span className="text-xs text-gray-500 dark:text-gray-400">{day.day}</span>
          <WeatherIcon icon={day.icon} size="small" />
          <div className="text-xs text-gray-700 dark:text-gray-300">
            {day.high !== null ? Math.round(day.high) : '—'}
            <span className="text-gray-400 dark:text-gray-500">
              /{day.low !== null ? Math.round(day.low) : '—'}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function WeatherWidget({ config }) {
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

  return (
    <div className="h-full flex flex-col">
      <div className="text-xs text-gray-500 dark:text-gray-400 text-right mb-1">
        {data.location}
      </div>
      <div className="flex-1 flex flex-col justify-center">
        <CurrentConditions current={data.current} units={config.units || 'imperial'} />
      </div>
      {data.forecast && data.forecast.length > 0 && (
        <Forecast forecast={data.forecast} units={config.units || 'imperial'} />
      )}
    </div>
  );
}
