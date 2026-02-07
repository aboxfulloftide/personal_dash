import { useState, useEffect } from 'react';
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

function PackageCard({ pkg, onDelete }) {
  const handleDelete = (e) => {
    e.preventDefault(); // Prevent opening tracking link
    e.stopPropagation();
    if (confirm(`Remove ${pkg.tracking_number} from tracking?`)) {
      onDelete(pkg.id);
    }
  };

  const getTrackingUrl = () => {
    const carrier = pkg.carrier.toLowerCase();
    const trackingNumber = encodeURIComponent(pkg.tracking_number);

    const urls = {
      usps: `https://tools.usps.com/go/TrackConfirmAction?tLabels=${trackingNumber}`,
      ups: `https://www.ups.com/track?tracknum=${trackingNumber}`,
      fedex: `https://www.fedex.com/fedextrack/?tracknumbers=${trackingNumber}`,
      amazon: pkg.tracking_number.includes('-')
        ? `https://www.amazon.com/progress-tracker/package/ref=ppx_yo_dt_b_track_package?_encoding=UTF8&orderId=${pkg.tracking_number}`
        : `https://track.amazon.com/tracking/${trackingNumber}`,
      dhl: `https://www.dhl.com/en/express/tracking.html?AWB=${trackingNumber}`,
    };

    return urls[carrier] || `https://www.google.com/search?q=${trackingNumber}+tracking`;
  };

  return (
    <a
      href={getTrackingUrl()}
      target="_blank"
      rel="noopener noreferrer"
      className={`block p-2 rounded border cursor-pointer transition-colors ${
        pkg.delivered
          ? 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800 hover:bg-green-100 dark:hover:bg-green-900/20'
          : 'bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <CarrierBadge carrier={pkg.carrier} />
        <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
          {truncateTracking(pkg.tracking_number)}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">↗</span>
        {pkg.delivered && (
          <span className="text-xs text-green-600 dark:text-green-400">✓</span>
        )}
        <button
          onClick={handleDelete}
          className="ml-auto text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
          title="Remove from tracking"
        >
          ✕
        </button>
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
    </a>
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

function EmailSetupModal({ isOpen, onClose, onSave, credentialId }) {
  const [provider, setProvider] = useState('gmail');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [scanInterval, setScanInterval] = useState('1');
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [testSuccess, setTestSuccess] = useState(false);
  const [existingCreds, setExistingCreds] = useState(null);

  const PROVIDERS = {
    gmail: { name: 'Gmail', server: 'imap.gmail.com', port: 993 },
    outlook: { name: 'Outlook', server: 'outlook.office365.com', port: 993 },
    yahoo: { name: 'Yahoo', server: 'imap.mail.yahoo.com', port: 993 },
    icloud: { name: 'iCloud', server: 'imap.mail.me.com', port: 993 },
    custom: { name: 'Custom', server: '', port: 993 },
  };

  const [customServer, setCustomServer] = useState('');
  const [customPort, setCustomPort] = useState('993');

  useEffect(() => {
    if (isOpen) {
      if (credentialId) {
        fetchExistingCredentials();
      } else {
        // Reset form for new credential
        setExistingCreds(null);
        setEmail('');
        setPassword('');
        setProvider('gmail');
        setScanInterval('1');
        setEnabled(true);
        setCustomServer('');
        setCustomPort('993');
        setError(null);
        setTestSuccess(false);
      }
    }
  }, [isOpen, credentialId]);

  const fetchExistingCredentials = async () => {
    try {
      const response = await api.get(`/email-credentials/${credentialId}`);
      if (response.data) {
        setExistingCreds(response.data);
        setEmail(response.data.email_address);
        setProvider(
          Object.keys(PROVIDERS).find(
            (key) => PROVIDERS[key].server === response.data.imap_server
          ) || 'custom'
        );
        if (response.data.imap_server && !Object.values(PROVIDERS).some(p => p.server === response.data.imap_server)) {
          setCustomServer(response.data.imap_server);
          setCustomPort(response.data.imap_port.toString());
        }
        setScanInterval(response.data.scan_interval_hours.toString());
        setEnabled(response.data.enabled);
      }
    } catch (err) {
      console.error('Failed to fetch credentials:', err);
      setError('Failed to load credential details');
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setError(null);
    setTestSuccess(false);

    const providerInfo = PROVIDERS[provider];
    const imapServer = provider === 'custom' ? customServer : providerInfo.server;
    const imapPort = provider === 'custom' ? parseInt(customPort) : providerInfo.port;

    try {
      await api.post('/email-credentials/test', {
        imap_server: imapServer,
        imap_port: imapPort,
        email_address: email,
        password: password,
      });
      setTestSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const providerInfo = PROVIDERS[provider];
    const imapServer = provider === 'custom' ? customServer : providerInfo.server;
    const imapPort = provider === 'custom' ? parseInt(customPort) : providerInfo.port;

    try {
      const payload = {
        imap_server: imapServer,
        imap_port: imapPort,
        email_address: email,
        enabled: enabled,
        scan_interval_hours: parseInt(scanInterval),
        days_to_scan: 30,
      };

      // Only include password if it's provided (for updates, password is optional)
      if (password) {
        payload.password = password;
      }

      if (credentialId) {
        await api.put(`/email-credentials/${credentialId}`, payload);
      } else {
        if (!password) {
          setError('Password is required for new setup');
          setLoading(false);
          return;
        }
        await api.post('/email-credentials', payload);
      }

      onSave();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this email account? This cannot be undone.')) return;

    setLoading(true);
    try {
      await api.delete(`/email-credentials/${credentialId}`);
      onSave();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete credentials');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {credentialId ? 'Edit Email Account' : 'Add Email Account'}
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {error && (
            <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded">{error}</div>
          )}
          {testSuccess && (
            <div className="text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-2 rounded">
              ✓ Connection successful!
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email Provider
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              {Object.entries(PROVIDERS).map(([key, { name }]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>
          </div>

          {provider === 'custom' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  IMAP Server
                </label>
                <input
                  type="text"
                  value={customServer}
                  onChange={(e) => setCustomServer(e.target.value.trim())}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="imap.example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  IMAP Port
                </label>
                <input
                  type="number"
                  value={customPort}
                  onChange={(e) => setCustomPort(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="993"
                  required
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {provider === 'gmail' ? 'App Password' : 'Password'} {credentialId ? '(leave blank to keep current)' : '*'}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              placeholder={credentialId ? '(unchanged)' : ''}
              required={!credentialId}
            />
            {provider === 'gmail' && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Get app password: <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">Google Account</a>
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Scan Frequency
            </label>
            <select
              value={scanInterval}
              onChange={(e) => setScanInterval(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              <option value="1">Every hour</option>
              <option value="6">Every 6 hours</option>
              <option value="12">Every 12 hours</option>
              <option value="24">Every 24 hours</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="enabled" className="text-sm text-gray-700 dark:text-gray-300">
              Enable auto-scanning
            </label>
          </div>

          <div className="flex justify-between gap-2 pt-2">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing || !email || !password}
              className="px-4 py-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 rounded-md text-sm disabled:opacity-50"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            <div className="flex gap-2">
              {credentialId && (
                <button
                  type="button"
                  onClick={handleDelete}
                  className="px-4 py-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded-md text-sm"
                >
                  Delete
                </button>
              )}
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !email || (!password && !credentialId)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
              >
                {loading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PackageTrackerWidget({ config }) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailAccounts, setEmailAccounts] = useState([]);
  const [editingCredentialId, setEditingCredentialId] = useState(null);

  const { data, loading, error, refresh } = useWidgetData({
    endpoint: '/packages',
    params: { include_delivered: config.show_delivered || false },
    refreshInterval: config.refresh_interval || 300,
  });

  const packages = data || [];

  useEffect(() => {
    fetchEmailAccounts();
  }, []);

  const fetchEmailAccounts = async () => {
    try {
      const response = await api.get('/email-credentials');
      setEmailAccounts(response.data || []);
    } catch (err) {
      console.error('Failed to fetch email accounts:', err);
      setEmailAccounts([]);
    }
  };

  const handleManualScan = async (credentialId) => {
    try {
      await api.post(`/email-credentials/${credentialId}/scan`);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Give it a moment
      refresh();
      fetchEmailAccounts();
    } catch (err) {
      console.error('Manual scan failed:', err);
      alert(err.response?.data?.detail || 'Failed to scan email');
    }
  };

  const handleDeletePackage = async (packageId) => {
    try {
      await api.delete(`/packages/${packageId}`);
      refresh();
    } catch (err) {
      console.error('Delete package failed:', err);
      alert(err.response?.data?.detail || 'Failed to delete package');
    }
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

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
      <div className="space-y-2 mb-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {packages.length} package{packages.length !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              + Add Package
            </button>
          </div>
        </div>

        {emailAccounts.length > 0 && (
          <div className="space-y-1">
            {emailAccounts.map((account) => (
              <div
                key={account.id}
                className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 p-2 rounded"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="flex items-center gap-1 flex-1 min-w-0">
                    <span>📧</span>
                    <span className="truncate" title={account.email_address}>
                      {account.email_address}
                    </span>
                    {account.enabled && (
                      <span>{account.last_scan_status === 'error' ? '⚠️' : '✓'}</span>
                    )}
                    {!account.enabled && (
                      <span className="text-gray-400">(off)</span>
                    )}
                  </span>
                  <div className="flex items-center gap-1">
                    {account.enabled && (
                      <button
                        onClick={() => handleManualScan(account.id)}
                        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 whitespace-nowrap"
                      >
                        Scan
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setEditingCredentialId(account.id);
                        setShowEmailModal(true);
                      }}
                      className="text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                      title="Edit email settings"
                    >
                      ⚙️
                    </button>
                  </div>
                </div>
                {account.last_scan_at && account.enabled && (
                  <div className="text-xs">
                    Last: {formatTimeAgo(account.last_scan_at)}
                    {account.packages_found_last_scan > 0 && (
                      <span> • {account.packages_found_last_scan} found</span>
                    )}
                  </div>
                )}
                {account.last_scan_status === 'error' && account.last_scan_message && (
                  <div className="text-xs text-red-500 mt-1">
                    {account.last_scan_message}
                  </div>
                )}
              </div>
            ))}
            <button
              onClick={() => {
                setEditingCredentialId(null);
                setShowEmailModal(true);
              }}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 w-full text-left"
            >
              + Add Email Account
            </button>
          </div>
        )}

        {emailAccounts.length === 0 && (
          <button
            onClick={() => {
              setEditingCredentialId(null);
              setShowEmailModal(true);
            }}
            className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 bg-gray-50 dark:bg-gray-800/50 p-2 rounded w-full text-left"
          >
            + Setup Email Scanning
          </button>
        )}
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
            <PackageCard key={pkg.id} pkg={pkg} onDelete={handleDeletePackage} />
          ))
        )}
      </div>

      <AddPackageModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={refresh}
      />

      <EmailSetupModal
        isOpen={showEmailModal}
        onClose={() => {
          setShowEmailModal(false);
          setEditingCredentialId(null);
        }}
        onSave={() => {
          refresh();
          fetchEmailAccounts();
        }}
        credentialId={editingCredentialId}
      />
    </div>
  );
}
