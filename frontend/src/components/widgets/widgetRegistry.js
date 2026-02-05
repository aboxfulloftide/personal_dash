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
    component: () => import('./PlaceholderWidget'),
    name: 'Stock Ticker',
    description: 'Real-time stock price tracking',
    category: 'finance',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 2, h: 1 },
    maxSize: { w: 6, h: 4 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Stock Ticker' },
      symbols: { type: 'text', label: 'Stock Symbols (comma-separated)', default: 'AAPL,GOOGL,MSFT', placeholder: 'AAPL,GOOGL,MSFT' },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 30, max: 3600, step: 30 },
    },
  },
  crypto_prices: {
    component: () => import('./PlaceholderWidget'),
    name: 'Crypto Prices',
    description: 'Cryptocurrency price tracking',
    category: 'finance',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 2, h: 1 },
    maxSize: { w: 6, h: 4 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Crypto Prices' },
      coins: { type: 'text', label: 'Coins (comma-separated)', default: 'bitcoin,ethereum', placeholder: 'bitcoin,ethereum,solana' },
      currency: {
        type: 'select', label: 'Display Currency', default: 'usd',
        options: [
          { value: 'usd', label: 'USD' },
          { value: 'eur', label: 'EUR' },
          { value: 'gbp', label: 'GBP' },
        ],
      },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 30, max: 3600, step: 30 },
    },
  },
  weather: {
    component: () => import('./PlaceholderWidget'),
    name: 'Weather',
    description: 'Current weather conditions and forecast',
    category: 'lifestyle',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 4, h: 4 },
    hasDataEndpoint: true,
    configSchema: {
      title: { type: 'text', label: 'Title', default: 'Weather' },
      location: { type: 'text', label: 'Location', placeholder: 'City name or zip code', required: true },
      units: {
        type: 'select', label: 'Units', default: 'imperial',
        options: [
          { value: 'imperial', label: 'Fahrenheit' },
          { value: 'metric', label: 'Celsius' },
        ],
      },
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', default: 300, min: 30, max: 3600, step: 30 },
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
