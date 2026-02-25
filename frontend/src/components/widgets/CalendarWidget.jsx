import { useState, useEffect, useRef } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';

function CalendarInstructions() {
  const [expandedProvider, setExpandedProvider] = useState(null);

  const providers = [
    {
      id: 'google',
      name: 'Google Calendar',
      icon: '🔵',
      steps: [
        'Open calendar.google.com',
        'Click Settings gear → Settings',
        'Select your calendar from the left sidebar',
        'Scroll to "Integrate calendar" section',
        'Copy the "Secret address in iCal format"',
        'Paste into widget settings',
      ],
    },
    {
      id: 'apple',
      name: 'Apple iCloud',
      icon: '🍎',
      steps: [
        'Open iCloud.com and sign in',
        'Click Calendar',
        'Click the share icon next to calendar name',
        'Enable "Public Calendar"',
        'Copy the URL',
        'Change webcal:// to https://',
        'Paste into widget settings',
      ],
    },
    {
      id: 'microsoft',
      name: 'Microsoft Outlook',
      icon: '📧',
      steps: [
        'Open outlook.office.com/calendar',
        'Click Settings → View all settings',
        'Go to Calendar → Shared calendars',
        'Select calendar and choose permissions',
        'Click "Publish"',
        'Copy the ICS link',
        'Paste into widget settings',
      ],
    },
  ];

  return (
    <div className="p-4 space-y-3 overflow-y-auto">
      <div className="text-center mb-4">
        <span className="text-4xl mb-2">📅</span>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-2">
          Add Your Calendar
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Click a provider below for setup instructions
        </p>
      </div>

      {providers.map((provider) => (
        <div
          key={provider.id}
          className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
        >
          <button
            onClick={() =>
              setExpandedProvider(expandedProvider === provider.id ? null : provider.id)
            }
            className="w-full px-3 py-2 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">{provider.icon}</span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {provider.name}
              </span>
            </div>
            <span className="text-gray-400">
              {expandedProvider === provider.id ? '−' : '+'}
            </span>
          </button>

          {expandedProvider === provider.id && (
            <div className="px-3 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
              <ol className="text-xs text-gray-600 dark:text-gray-400 space-y-1.5">
                {provider.steps.map((step, idx) => (
                  <li key={idx} className="flex gap-2">
                    <span className="flex-shrink-0 font-medium text-gray-400">
                      {idx + 1}.
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      ))}

      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-xs text-blue-800 dark:text-blue-300">
          <strong>💡 Tip:</strong> You can add multiple calendars by separating URLs
          with commas. Each will be color-coded!
        </p>
      </div>
    </div>
  );
}

// Calendar colors matching backend
const CALENDAR_COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#14b8a6', // Teal
  '#f97316', // Orange
  '#6366f1', // Indigo
  '#84cc16', // Lime
];

function formatTime(isoDateTime) {
  try {
    const date = new Date(isoDateTime);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return '';
  }
}

function formatDate(isoDate) {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '';
  }
}

function formatDateLong(isoDate) {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

function EventItem({ event, showDate = false }) {
  const color = CALENDAR_COLORS[event.source_index % CALENDAR_COLORS.length];

  return (
    <div className="flex gap-2 py-2 px-2 hover:bg-gray-50 dark:hover:bg-gray-700/30 rounded transition-colors">
      {/* Color indicator */}
      <div
        className="w-1 rounded flex-shrink-0"
        style={{ backgroundColor: color }}
      />

      <div className="flex-1 min-w-0">
        {/* Time or date */}
        <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">
          {event.all_day ? (
            <span>All day{showDate && ` • ${formatDate(event.start)}`}</span>
          ) : (
            <span>
              {formatTime(event.start)}
              {event.end && ` - ${formatTime(event.end)}`}
              {showDate && ` • ${formatDate(event.start)}`}
            </span>
          )}
        </div>

        {/* Title */}
        <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
          {event.title}
        </div>

        {/* Location */}
        {event.location && (
          <div className="text-xs text-gray-600 dark:text-gray-400 truncate mt-0.5">
            📍 {event.location}
          </div>
        )}

        {/* Source */}
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">
          {event.source}
        </div>
      </div>
    </div>
  );
}

function ViewTabs({ currentView, onViewChange, eventCounts = {} }) {
  const views = [
    { id: 'today', label: 'Today', count: eventCounts.today || 0 },
    { id: 'week', label: 'Week', count: eventCounts.week || 0 },
    { id: 'month', label: 'Month', count: eventCounts.month || 0 },
  ];

  return (
    <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 p-1 rounded">
      {views.map((view) => (
        <button
          key={view.id}
          onClick={() => onViewChange(view.id)}
          className={`flex-1 px-2 py-1.5 text-xs font-medium rounded transition-colors ${
            currentView === view.id
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          }`}
        >
          <div className="flex flex-col items-center">
            <span>{view.label}</span>
            <span className={`text-[10px] ${
              currentView === view.id
                ? 'text-gray-500 dark:text-gray-400'
                : 'text-gray-400 dark:text-gray-500'
            }`}>
              {view.count}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

function MonthSelector({ currentMonth, onMonthChange }) {
  // Parse year and month to avoid timezone issues
  const [year, month] = currentMonth.split('-').map(Number);
  const monthName = new Date(year, month - 1, 1).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  });

  return (
    <div className="flex items-center justify-between py-2 gap-2">
      <button
        type="button"
        onClick={() => {
          const [year, month] = currentMonth.split('-').map(Number);
          const prev = month === 1
            ? `${year - 1}-12`
            : `${year}-${String(month - 1).padStart(2, '0')}`;
          onMonthChange(prev);
        }}
        className="px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors text-gray-700 dark:text-gray-300"
        aria-label="Previous month"
      >
        ←
      </button>
      <div className="flex-1 text-sm font-medium text-gray-900 dark:text-gray-100 text-center">
        {monthName}
      </div>
      <button
        type="button"
        onClick={() => {
          const [year, month] = currentMonth.split('-').map(Number);
          const next = month === 12
            ? `${year + 1}-01`
            : `${year}-${String(month + 1).padStart(2, '0')}`;
          onMonthChange(next);
        }}
        className="px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors text-gray-700 dark:text-gray-300"
        aria-label="Next month"
      >
        →
      </button>
    </div>
  );
}

function EventsList({ events, view }) {
  if (events.length === 0) {
    const viewText = view === 'today' ? 'today' : view === 'week' ? 'this week' : 'this month';
    return (
      <div className="flex flex-col items-center justify-center h-32 text-gray-400 dark:text-gray-500">
        <span className="text-2xl mb-2">📅</span>
        <p className="text-sm">No events {viewText}</p>
        <p className="text-xs mt-1">Try switching to a different view</p>
      </div>
    );
  }

  // Group events by date for week/month views
  const groupByDate = view !== 'today';
  const grouped = {};

  if (groupByDate) {
    events.forEach((event) => {
      const dateKey = event.start.split('T')[0]; // Extract date part
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(event);
    });
  }

  if (groupByDate) {
    const sortedDates = Object.keys(grouped).sort();
    return (
      <div className="space-y-3">
        {sortedDates.map((date) => (
          <div key={date}>
            <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 px-2">
              {formatDateLong(date)}
            </div>
            <div className="space-y-1">
              {grouped[date].map((event, idx) => (
                <EventItem key={idx} event={event} showDate={false} />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {events.map((event, idx) => (
        <EventItem key={idx} event={event} showDate={false} />
      ))}
    </div>
  );
}

export default function CalendarWidget({ config }) {
  const defaultView = config.default_view || 'week';
  const [view, setView] = useState(defaultView);
  const [userOverrodeView, setUserOverrodeView] = useState(false);
  // Prevent auto-selection from re-firing on follow-up fetches (avoids week↔month cycle)
  const autoViewApplied = useRef(false);

  // For month view, track selected month
  const getCurrentMonth = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  };

  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth());

  // Reset to current month when switching to month view
  useEffect(() => {
    if (view === 'month') {
      setSelectedMonth(getCurrentMonth());
    }
  }, [view]);

  const { data, loading, error } = useWidgetData({
    endpoint: '/calendar',
    params: {
      calendars: config.calendars || '',
      view: view,
      month: view === 'month' ? selectedMonth : undefined,
      // Disable auto_fallback after initial selection to prevent week↔month cycle
      auto_fallback: !userOverrodeView && !autoViewApplied.current,
    },
    refreshInterval: config.refresh_interval || 600,
    enabled: !!config.calendars,
  });

  // Sync view with backend's auto-selected view (only once per session)
  useEffect(() => {
    if (data?.auto_selected_view && !userOverrodeView && !autoViewApplied.current) {
      autoViewApplied.current = true;
      setView(data.auto_selected_view);
    }
  }, [data?.auto_selected_view, userOverrodeView]);

  if (!config.calendars) {
    return <CalendarInstructions />;
  }

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <span className="text-2xl mb-2">📅</span>
        <p className="text-sm text-center text-red-500 mb-3">{error}</p>
        <div className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 max-w-sm">
          <p className="font-medium mb-2">Common issues:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li>Check if the ICS URL is correct</li>
            <li>Use the <strong>private/secret</strong> URL from your calendar</li>
            <li>Make sure the calendar is accessible</li>
            <li>Try refreshing the widget</li>
          </ul>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Handle view change - marks as manual override
  const handleViewChange = (newView) => {
    setView(newView);
    setUserOverrodeView(true);
  };

  // Handle month change - reset auto-fallback for new month
  const handleMonthChange = (newMonth) => {
    setSelectedMonth(newMonth);
    setUserOverrodeView(false);
    autoViewApplied.current = false; // Allow re-auto-selection for new month
  };

  // Get event counts for tabs
  const eventCounts = {
    today: data.events_today_count || 0,
    week: data.events_week_count || 0,
    month: data.events_month_count || 0,
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header with view tabs */}
      <div className="flex-shrink-0 mb-3">
        <ViewTabs
          currentView={view}
          onViewChange={handleViewChange}
          eventCounts={eventCounts}
        />
      </div>

      {/* Smart view indicator */}
      {data.auto_selected_view && !userOverrodeView && (
        <div className="flex-shrink-0 mb-2 px-2 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
          <p className="text-xs text-blue-800 dark:text-blue-300">
            <strong>Smart View:</strong> Showing{' '}
            {data.auto_selected_view === 'today' ? 'Today' :
             data.auto_selected_view === 'week' ? 'This Week' : 'This Month'}
            {' '}({eventCounts[data.auto_selected_view]} event{eventCounts[data.auto_selected_view] !== 1 ? 's' : ''})
          </p>
        </div>
      )}

      {/* Month selector for month view */}
      {view === 'month' && (
        <div className="flex-shrink-0">
          <MonthSelector
            currentMonth={selectedMonth}
            onMonthChange={handleMonthChange}
          />
        </div>
      )}

      {/* Events list - scrollable */}
      <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
        <EventsList events={data.events} view={view} />
      </div>

      {/* Footer with event count */}
      {data.events.length > 0 && (
        <div className="flex-shrink-0 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            {data.events.length} event{data.events.length !== 1 ? 's' : ''}
            {data.cached && ' • cached'}
          </div>
        </div>
      )}
    </div>
  );
}
