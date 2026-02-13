/**
 * AlertBadge - Displays severity indicator icon for alerted widgets
 */
export default function AlertBadge({ severity }) {
  const severityConfig = {
    critical: {
      icon: '🔴',
      label: 'Critical',
      color: 'text-red-600 dark:text-red-400',
    },
    warning: {
      icon: '⚠️',
      label: 'Warning',
      color: 'text-orange-600 dark:text-orange-400',
    },
    info: {
      icon: 'ℹ️',
      label: 'Info',
      color: 'text-blue-600 dark:text-blue-400',
    },
  };

  const config = severityConfig[severity] || severityConfig.info;

  return (
    <div className="flex items-center gap-1">
      <span className="text-lg" role="img" aria-label={config.label}>
        {config.icon}
      </span>
      <span className={`text-xs font-semibold uppercase ${config.color}`}>
        {config.label}
      </span>
    </div>
  );
}
