import { useState } from 'react';
import api from '../../services/api';

export default function FitnessLogModal({ isOpen, onClose, onSaved, defaultUnit = 'lbs' }) {
  const [formData, setFormData] = useState({
    weight: '',
    unit: defaultUnit,
    notes: '',
    recorded_at: new Date().toISOString().split('T')[0],
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      await api.post('/fitness/weight', {
        weight: parseFloat(formData.weight),
        unit: formData.unit,
        notes: formData.notes || null,
        recorded_at: formData.recorded_at,
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save weight entry');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-sm w-full">
        <form onSubmit={handleSubmit} className="p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Log Weight
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Date
            </label>
            <input
              type="date"
              value={formData.recorded_at}
              onChange={(e) => setFormData({ ...formData, recorded_at: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Weight
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                step="0.1"
                min="50"
                max="1000"
                placeholder={defaultUnit === 'lbs' ? '150.0' : '68.0'}
                required
                autoFocus
              />
              <select
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="lbs">lbs</option>
                <option value="kg">kg</option>
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
              Notes (optional)
            </label>
            <input
              type="text"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder="Morning, post-workout..."
            />
          </div>

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
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
