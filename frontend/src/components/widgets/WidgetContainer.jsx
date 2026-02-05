import { Suspense, lazy, useState } from 'react';
import { getWidget } from './widgetRegistry';

function WidgetLoader() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}

function WidgetError({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-red-500 p-4">
      <p className="text-sm text-center mb-2">{error || 'Failed to load widget'}</p>
      <button
        onClick={onRetry}
        className="text-xs text-blue-500 hover:underline"
      >
        Retry
      </button>
    </div>
  );
}

function RefreshIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}

export default function WidgetContainer({
  type,
  config = {},
  onRemove,
  onSettings,
  isEditing = false
}) {
  const [error, setError] = useState(null);
  const [retryKey, setRetryKey] = useState(0);

  const widgetDef = getWidget(type);
  const WidgetComponent = lazy(widgetDef.component);

  const handleRetry = () => {
    setError(null);
    setRetryKey(prev => prev + 1);
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      {/* Widget Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
          {config.title || widgetDef.name}
        </h3>
        <div className="flex items-center gap-1">
          {isEditing && (
            <>
              <button
                onClick={onSettings}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                title="Settings"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button
                onClick={onRemove}
                className="p-1 text-gray-400 hover:text-red-500"
                title="Remove"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Widget Content */}
      <div className="flex-1 overflow-auto p-3">
        {error ? (
          <WidgetError error={error} onRetry={handleRetry} />
        ) : (
          <Suspense fallback={<WidgetLoader />} key={retryKey}>
            <WidgetComponent config={config} />
          </Suspense>
        )}
      </div>
    </div>
  );
}
