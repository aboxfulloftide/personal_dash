import { useState } from 'react';
import api from '../../services/api';

/**
 * AcknowledgeButton - Button to acknowledge and clear widget alerts
 */
export default function AcknowledgeButton({ widgetId, onAcknowledge }) {
  const [isAcknowledging, setIsAcknowledging] = useState(false);

  const handleAcknowledge = async () => {
    setIsAcknowledging(true);
    try {
      await api.post(`/widgets/${widgetId}/acknowledge`);

      // Call parent callback to update UI
      if (onAcknowledge) {
        onAcknowledge(widgetId);
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    } finally {
      setIsAcknowledging(false);
    }
  };

  return (
    <button
      onClick={handleAcknowledge}
      disabled={isAcknowledging}
      className="flex-shrink-0 px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      title="Acknowledge and clear this alert"
    >
      {isAcknowledging ? 'Clearing...' : 'Acknowledge'}
    </button>
  );
}
