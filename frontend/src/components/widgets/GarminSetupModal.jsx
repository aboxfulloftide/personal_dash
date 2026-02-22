import { useState } from 'react';
import api from '../../services/api';

export default function GarminSetupModal({ isOpen, onClose, garminStatus, onStatusChange }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const isConnected = garminStatus?.connected;

  const handleConnect = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      const response = await api.post('/fitness/garmin/connect', { email, password });
      onStatusChange(response.data);
      setPassword('');
      setEmail('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect Garmin account');
    } finally {
      setSaving(false);
    }
  };

  const handleSync = async () => {
    setError(null);
    setSyncing(true);
    try {
      const response = await api.post('/fitness/garmin/sync');
      onStatusChange(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Disconnect Garmin account? Your synced data will remain.')) return;
    setError(null);
    try {
      await api.delete('/fitness/garmin/disconnect');
      onStatusChange({ connected: false });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disconnect');
    }
  };

  const formatLastSync = (ts) => {
    if (!ts) return 'Never';
    const d = new Date(ts);
    return d.toLocaleString();
  };

  const statusBadge = (status) => {
    const colors = {
      ok: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      never: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    };
    return colors[status] || colors.never;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Garmin Connect
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {isConnected ? (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Account</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {garminStatus.email}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Sync status</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(garminStatus.sync_status)}`}>
                    {garminStatus.sync_status}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Last synced</span>
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {formatLastSync(garminStatus.last_synced_at)}
                  </span>
                </div>
                {garminStatus.sync_error && (
                  <div className="text-xs text-red-500 dark:text-red-400 mt-1">
                    {garminStatus.sync_error}
                  </div>
                )}
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400">
                Syncs every 6 hours automatically. Steps, sleep, resting HR, and workouts are pulled from the last 7 days.
              </p>

              <div className="flex gap-2">
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 text-sm"
                >
                  {syncing ? 'Syncing...' : 'Sync Now'}
                </button>
                <button
                  onClick={handleDisconnect}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded text-sm"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleConnect} className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Connect your Garmin account to sync steps, sleep, heart rate, and workouts.
                Your password is used once to authenticate — only OAuth tokens are stored.
              </p>

              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                  Garmin Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                  Garmin Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Your Garmin Connect password"
                  required
                />
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400">
                Note: 2FA/MFA must be disabled on your Garmin account for this to work.
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded text-sm"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 text-sm"
                  disabled={saving}
                >
                  {saving ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
