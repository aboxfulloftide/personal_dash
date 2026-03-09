import { useState, useEffect } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import api from '../../services/api';
import ReminderModal from './ReminderModal';

/**
 * Check if a reminder has "tripped" (due time has passed).
 * All-day reminders and overdue reminders are always tripped.
 */
function isTripped(reminder) {
  if (reminder.is_overdue) return true;
  if (!reminder.due_time) return true; // all-day = always tripped

  const now = new Date();
  const [hour, minute] = reminder.due_time.split(':').map(Number);
  const dueDate = new Date(reminder.due_date + 'T00:00:00');
  dueDate.setHours(hour, minute, 0, 0);
  return now >= dueDate;
}

const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function formatRecurrence(reminder) {
  if (reminder.recurrence_type === 'day_of_week' && reminder.days_of_week) {
    const days = reminder.days_of_week.split(',').map(Number);
    if (days.length === 7) return 'Every day';
    if (days.length === 5 && [0,1,2,3,4].every(d => days.includes(d))) return 'Weekdays';
    return days.map(d => dayNames[d]).join(', ');
  }
  if (reminder.recurrence_type === 'interval') {
    const val = reminder.interval_value;
    const unit = reminder.interval_unit;
    if (val === 1) return `Every ${unit.replace(/s$/, '')}`;
    return `Every ${val} ${unit}`;
  }
  return '';
}

export default function ReminderWidget({ config = {}, isEditing = false }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editReminder, setEditReminder] = useState(null);
  const [loadingEdit, setLoadingEdit] = useState(null);
  const [allReminders, setAllReminders] = useState([]);
  const [loadingAll, setLoadingAll] = useState(false);

  const { data, loading, error, refresh } = useWidgetData({
    endpoint: '/reminders/instances/today',
    refreshInterval: (showAddModal || editReminder) ? 0 : 60,
  });

  // Fetch all reminder configs when entering edit mode
  useEffect(() => {
    if (isEditing) {
      fetchAllReminders();
    } else {
      setAllReminders([]);
    }
  }, [isEditing]);

  const fetchAllReminders = async () => {
    setLoadingAll(true);
    try {
      const res = await api.get('/reminders/?active_only=false');
      setAllReminders(res.data);
    } catch (err) {
      console.error('Failed to fetch reminders:', err);
    } finally {
      setLoadingAll(false);
    }
  };

  const handleEdit = async (reminderId) => {
    setLoadingEdit(reminderId);
    try {
      const res = await api.get(`/reminders/${reminderId}`);
      setEditReminder(res.data);
    } catch (err) {
      console.error('Failed to fetch reminder:', err);
    } finally {
      setLoadingEdit(null);
    }
  };

  const handleDismiss = async (instanceId) => {
    try {
      await api.post(`/reminders/instances/${instanceId}/dismiss`);
      refresh();
    } catch (err) {
      console.error('Failed to dismiss reminder:', err);
    }
  };

  const handleAcknowledge = async (instanceId) => {
    try {
      await api.post(`/reminders/instances/${instanceId}/acknowledge`);
      refresh();
    } catch (err) {
      console.error('Failed to acknowledge reminder:', err);
      alert(`Failed to acknowledge reminder: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSaved = () => {
    refresh();
    if (isEditing) fetchAllReminders();
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
        Failed to load reminders: {typeof error === 'string' ? error : error?.message || 'Unknown error'}
      </div>
    );
  }

  const reminders = data?.reminders || [];
  const pendingCount = data?.pending_count || 0;
  const dismissedCount = data?.dismissed_count || 0;
  const overdueCount = data?.overdue_count || 0;
  const activeCount = pendingCount + dismissedCount;

  // In edit mode, find reminder IDs that already have instances shown today
  const todayReminderIds = new Set(reminders.map(r => r.reminder_id));

  return (
    <div className="flex flex-col h-full">
      {/* Header stats */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {activeCount > 0 ? (
            <span>
              {pendingCount} pending
              {dismissedCount > 0 && `, ${dismissedCount} dismissed`}
              {overdueCount > 0 && ` (${overdueCount} overdue)`}
            </span>
          ) : (
            <span>All done!</span>
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
        {reminders.length === 0 && !isEditing ? (
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
            {reminders.map((reminder) => {
              const tripped = isTripped(reminder);
              const isDismissed = reminder.status === 'dismissed';
              const isPending = reminder.status === 'pending';
              const isUpcoming = isPending && !tripped;

              return (
                <div
                  key={reminder.instance_id}
                  className={`p-3 rounded border ${
                    isDismissed
                      ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
                      : reminder.is_overdue
                      ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                      : isUpcoming
                      ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-50'
                      : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                          {reminder.title}
                        </h3>
                        {reminder.is_overdue && isPending && (
                          <span className="text-xs bg-red-600 text-white px-1.5 py-0.5 rounded flex-shrink-0">
                            Overdue
                          </span>
                        )}
                        {isDismissed && (
                          <span className="text-xs bg-yellow-500 text-white px-1.5 py-0.5 rounded flex-shrink-0">
                            Dismissed
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
                        {isDismissed && reminder.dismissed_at && (
                          <span className="ml-2">
                            (Dismissed{' '}
                            {new Date(reminder.dismissed_at).toLocaleTimeString([], {
                              hour: 'numeric',
                              minute: '2-digit',
                            })}
                            )
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {/* Edit button - only in edit mode */}
                      {isEditing && (
                        <button
                          onClick={() => handleEdit(reminder.reminder_id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 text-sm"
                          title="Edit reminder"
                          disabled={loadingEdit === reminder.reminder_id}
                        >
                          {loadingEdit === reminder.reminder_id ? '...' : '✎'}
                        </button>
                      )}
                      {/* Tripped pending: show Dismiss + Ack */}
                      {isPending && tripped && (
                        <>
                          <button
                            onClick={() => handleDismiss(reminder.instance_id)}
                            className="text-yellow-600 hover:text-yellow-800 dark:text-yellow-400 dark:hover:text-yellow-300 text-lg p-1"
                            title="Dismiss (keep visible)"
                          >
                            ⏸
                          </button>
                          <button
                            onClick={() => handleAcknowledge(reminder.instance_id)}
                            className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 text-lg p-1"
                            title="Acknowledge (remove)"
                          >
                            ✓
                          </button>
                        </>
                      )}
                      {/* Dismissed: only Ack to clear */}
                      {isDismissed && (
                        <button
                          onClick={() => handleAcknowledge(reminder.instance_id)}
                          className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 text-lg p-1"
                          title="Acknowledge (remove)"
                        >
                          ✓
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* All reminders list - edit mode only */}
        {isEditing && (
          <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400 mb-2">
              All Reminders
            </h3>
            {loadingAll ? (
              <div className="text-xs text-gray-400 py-2">Loading...</div>
            ) : allReminders.length === 0 ? (
              <div className="text-xs text-gray-400 py-2">No reminders configured</div>
            ) : (
              <div className="space-y-1.5">
                {allReminders.map((r) => (
                  <div
                    key={r.id}
                    className={`flex items-center justify-between p-2 rounded border text-sm ${
                      r.is_active
                        ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                        : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 opacity-50'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                        {r.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {formatRecurrence(r)}
                        {r.reminder_time && ` at ${formatTime(r.reminder_time)}`}
                        {!r.is_active && ' (inactive)'}
                      </div>
                    </div>
                    <button
                      onClick={() => handleEdit(r.id)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 text-sm flex-shrink-0"
                      title="Edit reminder"
                      disabled={loadingEdit === r.id}
                    >
                      {loadingEdit === r.id ? '...' : '✎'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add Modal */}
      <ReminderModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSaved={() => {
          setShowAddModal(false);
          handleSaved();
        }}
      />

      {/* Edit Modal */}
      <ReminderModal
        isOpen={!!editReminder}
        onClose={() => setEditReminder(null)}
        onSaved={() => {
          setEditReminder(null);
          handleSaved();
        }}
        reminder={editReminder}
      />
    </div>
  );
}
