import { useState, useEffect, useCallback } from 'react';
import { getWidget, getWidgetConfigSchema } from './widgetRegistry';
import api from '../../services/api';

function ServerSelectField({ name, field, value, onChange }) {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchServers = async () => {
      try {
        const response = await api.get('/servers');
        setServers(response.data);
      } catch (err) {
        console.error('Failed to fetch servers:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchServers();
  }, []);

  const selectedIds = Array.isArray(value) ? value : (value ? [value] : []);

  const toggleServer = (serverId) => {
    const newSelected = selectedIds.includes(serverId)
      ? selectedIds.filter(id => id !== serverId)
      : [...selectedIds, serverId];
    onChange(name, newSelected.length > 0 ? newSelected : null);
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">Loading servers...</div>
    );
  }

  if (servers.length === 0) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">
        No servers available. <a href="/servers" className="text-blue-600 hover:underline">Add a server</a> first.
      </div>
    );
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {field.label} {field.required && <span className="text-red-500">*</span>}
      </label>
      <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-2">
        {servers.map((server) => (
          <label
            key={server.id}
            className="flex items-center gap-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selectedIds.includes(server.id)}
              onChange={() => toggleServer(server.id)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {server.name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {server.hostname || server.ip_address || `ID: ${server.id}`}
                {' • '}
                <span className={server.is_online ? 'text-green-600' : 'text-red-600'}>
                  {server.is_online ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </label>
        ))}
      </div>
      {selectedIds.length > 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {selectedIds.length} server{selectedIds.length !== 1 ? 's' : ''} selected
        </p>
      )}
    </div>
  );
}

function LocationSearchField({ name, field, value, onChange }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await api.get('/weather/locations/search', { params: { q: query } });
        setResults(response.data);
        setShowDropdown(true);
      } catch (err) {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (location) => {
    // Store coordinates as the location value for accurate geocoding
    const locationValue = `${location.latitude},${location.longitude}`;
    const displayName = location.admin1
      ? `${location.name}, ${location.admin1}`
      : `${location.name}, ${location.country}`;

    onChange(name, locationValue);
    onChange(`${name}_display`, displayName);
    setQuery(displayName);
    setShowDropdown(false);
  };

  // Initialize query from display name if we have a saved value
  useEffect(() => {
    if (value && !query) {
      // Check if there's a display name saved
      // This will be handled by the parent passing the display value
    }
  }, [value, query]);

  const id = `widget-config-${name}`;
  const displayValue = value ? (field.displayValue || query || value) : '';

  return (
    <div className="relative">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {field.label} {field.required && <span className="text-red-500">*</span>}
      </label>
      <input
        id={id}
        type="text"
        value={query || displayValue}
        placeholder={field.placeholder || 'Search for a city...'}
        onChange={(e) => {
          setQuery(e.target.value);
          if (e.target.value.length < 2) {
            setShowDropdown(false);
          }
        }}
        onFocus={() => results.length > 0 && setShowDropdown(true)}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      {loading && (
        <div className="absolute right-3 top-9">
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      )}
      {showDropdown && results.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
          {results.map((location) => (
            <button
              key={location.id}
              type="button"
              onClick={() => handleSelect(location)}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-white"
            >
              <div className="font-medium">
                {location.name}
                {location.admin1 && <span className="text-gray-500 dark:text-gray-400">, {location.admin1}</span>}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {location.country}
                {location.population && ` • Pop: ${location.population.toLocaleString()}`}
              </div>
            </button>
          ))}
        </div>
      )}
      {value && (
        <p className="mt-1 text-xs text-green-600 dark:text-green-400">
          Location set: {field.displayValue || value}
        </p>
      )}
    </div>
  );
}

function PingTargetsField({ name, field, value, onChange }) {
  const initialValue = value || field.default || [];
  const [targets, setTargets] = useState(initialValue);
  const [newHost, setNewHost] = useState('');
  const [newName, setNewName] = useState('');

  // Update local state when value prop changes (excluding initial mount)
  useEffect(() => {
    if (value !== undefined) {
      setTargets(value);
    }
  }, [value]);

  const handleAdd = () => {
    if (!newHost.trim()) return;
    const newTarget = {
      host: newHost.trim(),
      name: newName.trim() || newHost.trim(),
    };
    const updated = [...targets, newTarget];
    setTargets(updated);
    onChange(name, updated);
    setNewHost('');
    setNewName('');
  };

  const handleRemove = (index) => {
    const updated = targets.filter((_, i) => i !== index);
    setTargets(updated);
    onChange(name, updated.length > 0 ? updated : null);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {field.label}
      </label>

      {/* Existing targets list */}
      {targets.length > 0 && (
        <div className="space-y-2 mb-3 max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-2">
          {targets.map((target, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {target.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{target.host}</div>
              </div>
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="ml-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                title="Remove"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add new target form */}
      <div className="space-y-2">
        <input
          type="text"
          value={newHost}
          onChange={(e) => setNewHost(e.target.value)}
          placeholder="Host (e.g., 8.8.8.8 or google.com)"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Display name (optional)"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          type="button"
          onClick={handleAdd}
          disabled={!newHost.trim()}
          className="w-full px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Add Target
        </button>
      </div>

      {targets.length === 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          No targets configured. Add at least one host to monitor.
        </p>
      )}
    </div>
  );
}

function ConfigField({ name, field, value, onChange, config }) {
  const id = `widget-config-${name}`;

  switch (field.type) {
    case 'text':
      return (
        <div>
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {field.label} {field.required && <span className="text-red-500">*</span>}
          </label>
          <input
            id={id}
            type="text"
            value={value ?? field.default ?? ''}
            placeholder={field.placeholder || ''}
            onChange={(e) => onChange(name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      );

    case 'number':
      return (
        <div>
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {field.label} {field.required && <span className="text-red-500">*</span>}
          </label>
          <input
            id={id}
            type="number"
            value={value ?? field.default ?? ''}
            min={field.min}
            max={field.max}
            step={field.step}
            onChange={(e) => onChange(name, e.target.value === '' ? null : Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      );

    case 'select':
      return (
        <div>
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {field.label}
          </label>
          <select
            id={id}
            value={value ?? field.default ?? ''}
            onChange={(e) => onChange(name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {(field.options || []).map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      );

    case 'toggle':
      return (
        <div className="flex items-center justify-between">
          <label htmlFor={id} className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {field.label}
          </label>
          <button
            id={id}
            type="button"
            role="switch"
            aria-checked={value ?? field.default ?? false}
            onClick={() => onChange(name, !(value ?? field.default ?? false))}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              (value ?? field.default ?? false)
                ? 'bg-blue-600'
                : 'bg-gray-300 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                (value ?? field.default ?? false) ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      );

    case 'location_search':
      return (
        <LocationSearchField
          name={name}
          field={{ ...field, displayValue: config[`${name}_display`] }}
          value={value}
          onChange={onChange}
        />
      );

    case 'server_select':
      return (
        <ServerSelectField
          name={name}
          field={field}
          value={value}
          onChange={onChange}
        />
      );

    case 'ping_targets':
      return (
        <PingTargetsField
          name={name}
          field={field}
          value={value}
          onChange={onChange}
        />
      );

    default:
      return null;
  }
}

export default function WidgetSettingsModal({ isOpen, widgetId, widgetType, currentConfig, onSave, onClose }) {
  const [config, setConfig] = useState({});
  const widgetDef = getWidget(widgetType);
  const schema = getWidgetConfigSchema(widgetType);

  useEffect(() => {
    if (isOpen) {
      // Initialize config with defaults for any missing fields
      const configWithDefaults = { ...currentConfig };
      Object.entries(schema).forEach(([key, field]) => {
        if (configWithDefaults[key] === undefined && field.default !== undefined) {
          configWithDefaults[key] = field.default;
        }
      });
      setConfig(configWithDefaults);
    }
  }, [isOpen, currentConfig, schema]);

  if (!isOpen) return null;

  const handleFieldChange = (name, value) => {
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    onSave(widgetId, config);
    onClose();
  };

  const schemaEntries = Object.entries(schema);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {widgetDef?.name || 'Widget'} Settings
          </h2>
        </div>

        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          {schemaEntries.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No settings available for this widget.
            </p>
          ) : (
            schemaEntries.map(([name, field]) => (
              <ConfigField
                key={name}
                name={name}
                field={field}
                value={config[name]}
                onChange={handleFieldChange}
                config={config}
              />
            ))
          )}
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
