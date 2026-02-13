import AlertBadge from './AlertBadge';
import AcknowledgeButton from './AcknowledgeButton';

/**
 * AlertBanner - Displays alert message bar within widget
 */
export default function AlertBanner({ severity, message, onAcknowledge, widgetId }) {
  const severityStyles = {
    critical: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800',
    warning: 'bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800',
    info: 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800',
  };

  const style = severityStyles[severity] || severityStyles.info;

  return (
    <div className={`${style} border rounded-md p-3 mb-3`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <AlertBadge severity={severity} />
          <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
            {message}
          </p>
        </div>
        <AcknowledgeButton onAcknowledge={onAcknowledge} widgetId={widgetId} />
      </div>
    </div>
  );
}
