// Widget registry - add new widgets here
// Each entry defines the component, metadata, sizing, and config schema.
// The configSchema drives the WidgetSettingsModal form dynamically.

const widgetRegistry = {
  server_monitor: {
    component: () => import('./ServerMonitorWidget'),
    name: 'Server Monitor',
    description: 'Monitor server CPU, memory, disk, and Docker containers',
    category: 'monitoring',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 6 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Server Monitor' },
      server_id: { type: 'number', label: 'Server ID', required: true },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 60, min: 10, max: 3600, step: 10 },
      show_docker: { type: 'toggle', label: 'Show Docker Containers', default: true },
    },
  },
  package_tracker: {
    component: () => import('./PackageTrackerWidget'),
    name: 'Package Tracker',
    description: 'Track packages from USPS, UPS, FedEx, and Amazon',
    category: 'lifestyle',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 6 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Package Tracker' },
      show_delivered: { type: 'toggle', label: 'Show Delivered Packages', default: false },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 30, max: 3600, step: 30 },
    },
  },
  stock_ticker: {
    component: () => import('./StockTickerWidget'),
    name: 'Stock Ticker',
    description: 'Track stock prices and portfolio value',
    category: 'finance',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 5 },
    hasDataEndpoint: true,
    supportsConfigChange: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Stock Ticker' },
      api_provider: {
        type: 'select', label: 'API Provider', default: 'yahoo',
        options: [
          { value: 'yahoo', label: 'Yahoo Finance (free, no key)' },
          { value: 'alphavantage', label: 'Alpha Vantage (25/day, key required)' },
          { value: 'finnhub', label: 'Finnhub (60/min, key required)' },
        ],
      },
      api_key: { type: 'text', label: 'API Key (optional)', placeholder: 'Your API key for higher limits' },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 60, max: 3600, step: 60 },
    },
  },
  crypto_prices: {
    component: () => import('./CryptoWidget'),
    name: 'Crypto Prices',
    description: 'Track cryptocurrency prices and portfolio value',
    category: 'finance',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 5 },
    hasDataEndpoint: true,
    supportsConfigChange: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Crypto Prices' },
      api_provider: {
        type: 'select', label: 'API Provider', default: 'coingecko',
        options: [
          { value: 'coingecko', label: 'CoinGecko (free, no key)' },
          { value: 'coincap', label: 'CoinCap (free, no key)' },
        ],
      },
      api_key: { type: 'text', label: 'API Key (optional)', placeholder: 'Your API key for higher limits' },
      currency: {
        type: 'select', label: 'Display Currency', default: 'usd',
        options: [
          { value: 'usd', label: 'USD' },
          { value: 'eur', label: 'EUR' },
          { value: 'gbp', label: 'GBP' },
        ],
      },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 60, max: 3600, step: 60 },
    },
  },
  weather: {
    component: () => import('./WeatherWidget'),
    name: 'Weather',
    description: 'Current weather conditions, hourly and 5-day forecast',
    category: 'lifestyle',
    defaultSize: { w: 3, h: 4 },
    minSize: { w: 2, h: 3 },
    maxSize: { w: 4, h: 5 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Weather' },
      location: { type: 'location_search', label: 'Location', placeholder: 'Search for a city...', required: true },
      api_provider: {
        type: 'select', label: 'API Provider', default: 'openmeteo',
        options: [
          { value: 'openmeteo', label: 'Open-Meteo (free, no key)' },
          { value: 'openweathermap', label: 'OpenWeatherMap (1000/day, key required)' },
        ],
      },
      api_key: { type: 'text', label: 'API Key (for OpenWeatherMap)', placeholder: 'Your API key' },
      units: {
        type: 'select', label: 'Units', default: 'imperial',
        options: [
          { value: 'imperial', label: 'Fahrenheit' },
          { value: 'metric', label: 'Celsius' },
        ],
      },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 900, min: 300, max: 3600, step: 300 },
    },
  },
  fitness: {
    component: () => import('./PlaceholderWidget'),
    name: 'Fitness Stats',
    description: 'Body weight tracking with charts',
    category: 'lifestyle',
    defaultSize: { w: 3, h: 2 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 4 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Fitness Stats' },
      days: { type: 'number', label: 'Days to Show', default: 30, min: 7, max: 365, step: 1 },
      goal_weight: { type: 'number', label: 'Goal Weight', min: 50, max: 500, step: 0.1 },
    },
  },
  news_headlines: {
    component: () => import('./NewsWidget'),
    name: 'News Headlines',
    description: 'Aggregated RSS news feeds with optional NewsAPI.org support',
    category: 'lifestyle',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 6 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'News Headlines' },
      provider: {
        type: 'select', label: 'Provider', default: 'rss',
        options: [
          { value: 'rss', label: 'RSS Feed' },
          { value: 'newsapi', label: 'NewsAPI.org' },
        ],
      },
      source: {
        type: 'text',
        label: 'News Sources (comma-separated)',
        default: 'bbc,techcrunch',
        placeholder: 'bbc,techcrunch,npr (available: bbc,npr,reuters,cnn,techcrunch,hackernews,custom)'
      },
      custom_url: { type: 'text', label: 'Custom RSS URL', placeholder: 'https://example.com/feed.xml' },
      api_key: { type: 'text', label: 'NewsAPI.org Key (optional)', placeholder: 'Your NewsAPI.org API key' },
      category: {
        type: 'select', label: 'NewsAPI Category', default: 'general',
        options: [
          { value: 'general', label: 'General' },
          { value: 'business', label: 'Business' },
          { value: 'technology', label: 'Technology' },
          { value: 'sports', label: 'Sports' },
          { value: 'entertainment', label: 'Entertainment' },
          { value: 'science', label: 'Science' },
          { value: 'health', label: 'Health' },
        ],
      },
      max_articles: { type: 'number', label: 'Max Articles', default: 10, min: 5, max: 50, step: 5 },
      include_keywords: { type: 'text', label: 'Include Keywords (comma-separated)', placeholder: 'tech, AI, startup (only show articles with these words)' },
      exclude_keywords: { type: 'text', label: 'Exclude Keywords (comma-separated)', placeholder: 'apple, politics (hide articles with these words)' },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 600, min: 300, max: 3600, step: 60 },
    },
  },
};

const fallbackWidget = {
  component: () => import('./PlaceholderWidget'),
  name: 'Unknown Widget',
  description: 'Unknown widget type',
  category: 'other',
  defaultSize: { w: 2, h: 2 },
  minSize: { w: 1, h: 1 },
  maxSize: { w: 4, h: 4 },
  configSchema: {},
};

export function getWidget(type) {
  return widgetRegistry[type] || fallbackWidget;
}

export function getAvailableWidgets() {
  return Object.entries(widgetRegistry).map(([type, config]) => ({
    type,
    name: config.name,
    description: config.description,
    category: config.category,
    defaultSize: config.defaultSize,
  }));
}

export function getWidgetConfigSchema(type) {
  const widget = widgetRegistry[type];
  return widget?.configSchema || {};
}

export default widgetRegistry;
