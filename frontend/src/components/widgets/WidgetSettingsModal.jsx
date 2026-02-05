import { useState, useEffect } from 'react';
import { getWidget, getWidgetConfigSchema } from './widgetRegistry';

function ConfigField({ name, field, value, onChange }) {
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
      setConfig({ ...currentConfig });
    }
  }, [isOpen, currentConfig]);

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
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {widgetDef?.name || 'Widget'} Settings
          </h2>
        </div>

        <div className="p-4 overflow-y-auto max-h-96 space-y-4">
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
              />
            ))
          )}
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
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
