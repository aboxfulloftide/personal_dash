import AcknowledgeButton from './AcknowledgeButton';

const SEVERITY_CONFIG = {
  critical: {
    icon: '🔴',
    label: 'Critical',
    borderClass: 'border-red-500 dark:border-red-600',
    bgClass: 'bg-red-50 dark:bg-red-900/30',
    labelClass: 'text-red-700 dark:text-red-300',
  },
  warning: {
    icon: '⚠️',
    label: 'Warning',
    borderClass: 'border-orange-500 dark:border-orange-600',
    bgClass: 'bg-orange-50 dark:bg-orange-900/30',
    labelClass: 'text-orange-700 dark:text-orange-300',
  },
  info: {
    icon: 'ℹ️',
    label: 'Info',
    borderClass: 'border-blue-500 dark:border-blue-600',
    bgClass: 'bg-blue-50 dark:bg-blue-900/30',
    labelClass: 'text-blue-700 dark:text-blue-300',
  },
};

/**
 * AlertsOverlay
 *
 * Renders active alerts as floating cards pinned to the top-center of the
 * viewport, overlaying the dashboard without touching the grid layout at all.
 *
 * Each card shows:
 *   - Severity icon + label — widget title
 *   - Alert message
 *   - Acknowledge button (clears the alert)
 *
 * The outer wrapper uses pointer-events-none so the overlay never blocks
 * clicks on the dashboard behind it; individual cards opt back in with
 * pointer-events-auto.
 */
export default function AlertsOverlay({ alertedWidgets, onAcknowledge }) {
  if (!alertedWidgets || alertedWidgets.length === 0) return null;

  // Sort: critical first, then warning, then info
  const sorted = [...alertedWidgets].sort((a, b) => {
    const order = { critical: 0, warning: 1, info: 2 };
    return (order[a.alert_severity] ?? 3) - (order[b.alert_severity] ?? 3);
  });

  return (
    <div
      className="fixed top-16 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 w-full max-w-lg px-4 pointer-events-none"
      aria-live="polite"
      aria-label="Active alerts"
    >
      {sorted.map((widget) => {
        const sev = SEVERITY_CONFIG[widget.alert_severity] || SEVERITY_CONFIG.info;
        const title = widget.config?.title || widget.type;

        return (
          <div
            key={widget.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-lg border-2 ${sev.borderClass} ${sev.bgClass} px-4 py-3 shadow-xl`}
          >
            <span className="text-lg flex-shrink-0 mt-0.5" aria-hidden="true">
              {sev.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-bold uppercase tracking-wide ${sev.labelClass}`}>
                {sev.label} — {title}
              </p>
              <p className="text-sm text-gray-800 dark:text-gray-100 mt-0.5 leading-snug">
                {widget.alert_message}
              </p>
            </div>
            <AcknowledgeButton widgetId={widget.id} onAcknowledge={onAcknowledge} />
          </div>
        );
      })}
    </div>
  );
}
