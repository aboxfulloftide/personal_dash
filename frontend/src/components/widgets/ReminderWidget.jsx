import { useState } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import api from '../../services/api';
import ReminderModal from './ReminderModal';

export default function ReminderWidget({ config = {} }) {
  const [showAddModal, setShowAddModal] = useState(false);

  // Fetch today's reminders
  const { data, loading, error, refetch } = useWidgetData({
    endpoint: '/reminders/instances/today',
    refreshInterval: 60, // Refresh every minute
  });

  const handleDismiss = async (instanceId) => {
    try {
      await api.post(`/reminders/instances/${instanceId}/dismiss`);
      refetch(); // Refresh the list
    } catch (err) {
      console.error('Failed to dismiss reminder:', err);
    }
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    const [hour, minute] = timeString.split(':');
    const hourNum = parseInt(hour, 10);
    const ampm = hourNum >= 12 ? 'PM' : 'AM';
    const hour12 = hourNum % 12 || 12;
    return `${hour12}:${minute} ${ampm}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-gray-500 dark:text-gray-400">Loading reminders...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 dark:text-red-400 text-sm p-4">
        Failed to load reminders: {error.message || 'Unknown error'}
      </div>
    );
  }

  const reminders = data?.reminders || [];
  const pendingCount = data?.pending_count || 0;
  const overdueCount = data?.overdue_count || 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header stats */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {pendingCount > 0 ? (
            <span>
              {pendingCount} pending{overdueCount > 0 && ` (${overdueCount} overdue)`}
            </span>
          ) : (
            <span>All done! 🎉</span>
          )}
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
        >
          + Add
        </button>
      </div>

      {/* Reminders list */}
      <div className="flex-1 overflow-auto scrollbar-hide">
        {reminders.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <div className="text-4xl mb-2">📝</div>
            <div className="text-sm">No reminders for today</div>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-3 text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              Create your first reminder
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {reminders.map((reminder) => (
              <div
                key={reminder.instance_id}
                className={`p-3 rounded border ${
                  reminder.status === 'dismissed'
                    ? 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-50'
                    : reminder.is_overdue
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                        {reminder.title}
                      </h3>
                      {reminder.is_overdue && reminder.status === 'pending' && (
                        <span className="text-xs bg-red-600 text-white px-1.5 py-0.5 rounded flex-shrink-0">
                          Overdue
                        </span>
                      )}
                      {reminder.instance_number && (
                        <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                          #{reminder.instance_number}
                        </span>
                      )}
                    </div>

                    {reminder.notes && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1 line-clamp-2">
                        {reminder.notes}
                      </p>
                    )}

                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      {reminder.due_time ? formatTime(reminder.due_time) : 'All day'}
                      {reminder.status === 'dismissed' && reminder.dismissed_at && (
                        <span className="ml-2">
                          (Completed{' '}
                          {new Date(reminder.dismissed_at).toLocaleTimeString([], {
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                          )
                        </span>
                      )}
                    </div>
                  </div>

                  {reminder.status === 'pending' && (
                    <button
                      onClick={() => handleDismiss(reminder.instance_id)}
                      className="flex-shrink-0 text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 text-xl"
                      title="Mark as complete"
                    >
                      ✓
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      <ReminderModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSaved={() => {
          setShowAddModal(false);
          refetch();
        }}
      />
    </div>
  );
}
