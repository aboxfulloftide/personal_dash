import { useState } from 'react';
import api from '../../services/api';

export default function ReminderModal({ isOpen, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    title: '',
    notes: '',
    recurrence_type: 'day_of_week',
    interval_value: 1,
    interval_unit: 'days',
    days_of_week: [],
    reminder_time: '09:00',
    start_date: new Date().toISOString().split('T')[0],
    carry_over: true,
    is_active: true,
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      // Prepare data for API
      const submitData = {
        ...formData,
        days_of_week: formData.recurrence_type === 'day_of_week'
          ? formData.days_of_week.join(',')
          : null,
        interval_value: formData.recurrence_type === 'interval'
          ? parseInt(formData.interval_value, 10)
          : null,
        interval_unit: formData.recurrence_type === 'interval'
          ? formData.interval_unit
          : null,
        reminder_time: formData.reminder_time || null,
      };

      await api.post('/reminders/', submitData);
      onSaved();
      onClose();
    } catch (err) {
      console.error('Failed to create reminder:', err);
      setError(err.response?.data?.detail || 'Failed to create reminder');
    } finally {
      setSaving(false);
    }
  };

  const toggleDayOfWeek = (day) => {
    const days = [...formData.days_of_week];
    const index = days.indexOf(day);
    if (index > -1) {
      days.splice(index, 1);
    } else {
      days.push(day);
    }
    setFormData({ ...formData, days_of_week: days.sort() });
  };

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Add Reminder
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {/* Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              required
              placeholder="e.g., Take vitamins"
            />
          </div>

          {/* Notes */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Notes (optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              rows="2"
              placeholder="Additional details..."
            />
          </div>

          {/* Recurrence Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Repeat
            </label>
            <select
              value={formData.recurrence_type}
              onChange={(e) => setFormData({ ...formData, recurrence_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="day_of_week">Specific days of week</option>
              <option value="interval">Every N days/hours/weeks/months</option>
            </select>
          </div>

          {/* Days of Week */}
          {formData.recurrence_type === 'day_of_week' && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Days *
              </label>
              <div className="flex gap-2 flex-wrap">
                {dayNames.map((day, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => toggleDayOfWeek(index)}
                    className={`px-3 py-1 rounded text-sm ${
                      formData.days_of_week.includes(index)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Interval */}
          {formData.recurrence_type === 'interval' && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                Every
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={formData.interval_value}
                  onChange={(e) => setFormData({ ...formData, interval_value: e.target.value })}
                  className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  min="1"
                  required
                />
                <select
                  value={formData.interval_unit}
                  onChange={(e) => setFormData({ ...formData, interval_unit: e.target.value })}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="hours">Hour(s)</option>
                  <option value="days">Day(s)</option>
                  <option value="weeks">Week(s)</option>
                  <option value="months">Month(s)</option>
                </select>
              </div>
            </div>
          )}

          {/* Time */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Time {formData.recurrence_type === 'interval' && formData.interval_unit === 'hours' ? '(for first reminder)' : ''}
            </label>
            <input
              type="time"
              value={formData.reminder_time}
              onChange={(e) => setFormData({ ...formData, reminder_time: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Start Date */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Start Date
            </label>
            <input
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              required
            />
          </div>

          {/* Carry Over */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={formData.carry_over}
                onChange={(e) => setFormData({ ...formData, carry_over: e.target.checked })}
                className="rounded"
              />
              <span>Carry over missed reminders to next day</span>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
              If unchecked, missed reminders will be auto-dismissed
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
