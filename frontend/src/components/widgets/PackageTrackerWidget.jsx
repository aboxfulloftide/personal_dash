import { useState } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import api from '../../services/api';

const CARRIERS = {
  usps: { name: 'USPS', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  ups: { name: 'UPS', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  fedex: { name: 'FedEx', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
  amazon: { name: 'Amazon', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  dhl: { name: 'DHL', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  other: { name: 'Other', color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
};

function formatDate(dateStr) {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function truncateTracking(tracking) {
  if (tracking.length <= 12) return tracking;
  return `${tracking.slice(0, 6)}...${tracking.slice(-4)}`;
}

function CarrierBadge({ carrier }) {
  const info = CARRIERS[carrier] || CARRIERS.other;
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${info.color}`}>
      {info.name}
    </span>
  );
}

function PackageCard({ pkg }) {
  return (
    <div className={`p-2 rounded border ${
      pkg.delivered
        ? 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800'
        : 'bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-700'
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <CarrierBadge carrier={pkg.carrier} />
        <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
          {truncateTracking(pkg.tracking_number)}
        </span>
        {pkg.delivered && (
          <span className="text-xs text-green-600 dark:text-green-400 ml-auto">✓</span>
        )}
      </div>
      {pkg.description && (
        <p className="text-sm text-gray-700 dark:text-gray-300 truncate mb-1">
          {pkg.description}
        </p>
      )}
      <div className="text-xs text-gray-500 dark:text-gray-400">
        {pkg.status || 'Awaiting update'}
        {pkg.estimated_delivery && !pkg.delivered && (
          <span> • Est. {formatDate(pkg.estimated_delivery)}</span>
        )}
      </div>
    </div>
  );
}

function AddPackageModal({ isOpen, onClose, onAdd }) {
  const [tracking, setTracking] = useState('');
  const [carrier, setCarrier] = useState('usps');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!tracking.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await api.post('/packages', {
        tracking_number: tracking.trim(),
        carrier,
        description: description.trim() || null,
      });
      setTracking('');
      setCarrier('usps');
      setDescription('');
      onAdd();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add package');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Add Package</h3>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tracking Number *
            </label>
            <input
              type="text"
              value={tracking}
              onChange={(e) => setTracking(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              placeholder="1Z999AA10123456784"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Carrier *
            </label>
            <select
              value={carrier}
              onChange={(e) => setCarrier(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              {Object.entries(CARRIERS).map(([value, { name }]) => (
                <option key={value} value={value}>{name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              placeholder="New laptop"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !tracking.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {loading ? 'Adding...' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PackageTrackerWidget({ config }) {
  const [showAddModal, setShowAddModal] = useState(false);

  const { data, loading, error, refresh } = useWidgetData({
    endpoint: '/packages',
    params: { include_delivered: config.show_delivered || false },
    refreshInterval: config.refresh_interval || 300,
  });

  const packages = data || [];

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500">
        <p className="text-sm text-center">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {packages.length} package{packages.length !== 1 ? 's' : ''}
        </span>
        <button
          onClick={() => setShowAddModal(true)}
          className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          + Add
        </button>
      </div>

      <div className="flex-1 overflow-auto space-y-2">
        {packages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
            <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p className="text-sm">No packages</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="text-xs text-blue-500 hover:underline mt-1"
            >
              Add a package to track
            </button>
          </div>
        ) : (
          packages.map((pkg) => (
            <PackageCard key={pkg.id} pkg={pkg} />
          ))
        )}
      </div>

      <AddPackageModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={refresh}
      />
    </div>
  );
}
