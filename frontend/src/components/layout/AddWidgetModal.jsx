import { useState } from 'react';
import { getAvailableWidgets } from '../widgets/widgetRegistry';

export default function AddWidgetModal({ isOpen, onClose, onAdd }) {
  const [selectedType, setSelectedType] = useState(null);
  const availableWidgets = getAvailableWidgets();

  if (!isOpen) return null;

  const handleAdd = () => {
    if (selectedType) {
      onAdd(selectedType);
      setSelectedType(null);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add Widget
          </h2>
        </div>

        <div className="p-4 overflow-y-auto max-h-96">
          <div className="grid gap-2">
            {availableWidgets.map((widget) => (
              <button
                key={widget.type}
                onClick={() => setSelectedType(widget.type)}
                className={`p-3 text-left rounded-lg border-2 transition-colors ${
                  selectedType === widget.type
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="font-medium text-gray-900 dark:text-white">
                  {widget.name}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {widget.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleAdd}
            disabled={!selectedType}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Widget
          </button>
        </div>
      </div>
    </div>
  );
}
