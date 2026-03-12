import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

// Used only for env file content generation (not for API calls)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// ─── Temperature helpers ──────────────────────────────────────────────────────

function toF(c) { return c * 9 / 5 + 32; }

function formatTemp(celsius, unit) {
  if (celsius == null) return '—';
  const val = unit === 'F' ? toF(celsius) : celsius;
  return `${val.toFixed(1)}°${unit}`;
}

// Thresholds in Celsius regardless of display unit
function tempColor(celsius) {
  if (celsius == null) return 'text-blue-600 dark:text-blue-400';
  if (celsius >= 90) return 'text-red-500 dark:text-red-400';
  if (celsius >= 80) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-blue-600 dark:text-blue-400';
}

function tempBg(celsius) {
  if (celsius >= 90) return 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800';
  if (celsius >= 80) return 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800';
  return 'bg-gray-50 dark:bg-gray-700/50';
}

function tempEmoji(celsius) {
  if (celsius >= 90) return '🌡️';
  if (celsius >= 80) return '🔥';
  return '❄️';
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatBytes(bytes) {
  if (bytes == null) return '—';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

// Ensure naive UTC strings from the backend are parsed as UTC, not local time
function parseUTC(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z');
}

function formatTime(dateStr) {
  if (!dateStr) return '—';
  return parseUTC(dateStr).toLocaleString();
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return '—';
  const diff = Math.floor((Date.now() - parseUTC(dateStr)) / 1000);
  if (diff < 0) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function metricColor(pct) {
  if (pct == null) return 'text-gray-400';
  if (pct >= 90) return 'text-red-500';
  if (pct >= 70) return 'text-yellow-500';
  return 'text-green-500';
}

function metricBarColor(pct) {
  if (pct == null) return 'bg-gray-300 dark:bg-gray-600';
  if (pct >= 90) return 'bg-red-500';
  if (pct >= 70) return 'bg-yellow-500';
  return 'bg-green-500';
}

// ─── Modals ───────────────────────────────────────────────────────────────────

function AddServerModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '', hostname: '', ip_address: '', mac_address: '', poll_interval: 60,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) { setError('Server name is required'); return; }
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.post('/servers', formData);
      onSuccess(res.data);
      setFormData({ name: '', hostname: '', ip_address: '', mac_address: '', poll_interval: 60 });
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create server');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Register New Server</h3>
        {error && <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md text-sm">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {[
              { label: 'Server Name *', key: 'name', placeholder: 'my-server', required: true },
              { label: 'Hostname (optional)', key: 'hostname', placeholder: 'server.example.com' },
              { label: 'IP Address (optional)', key: 'ip_address', placeholder: '192.168.1.100' },
              { label: 'MAC Address (optional, for Wake-on-LAN)', key: 'mac_address', placeholder: '00:11:22:33:44:55' },
            ].map(({ label, key, placeholder, required }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                <input
                  type="text"
                  value={formData[key]}
                  onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
                  placeholder={placeholder}
                  required={required}
                  disabled={submitting}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            ))}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Poll Interval (seconds)</label>
              <input
                type="number"
                value={formData.poll_interval}
                onChange={(e) => setFormData({ ...formData, poll_interval: parseInt(e.target.value) })}
                min="10" max="3600"
                disabled={submitting}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <button type="button" onClick={onClose} disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50">
              Cancel
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {submitting ? 'Creating...' : 'Create Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ApiKeyModal({ isOpen, onClose, serverData }) {
  const [copied, setCopied] = useState(false);
  if (!isOpen || !serverData) return null;
  const { server, api_key } = serverData;

  const envContent = `# Personal Dash Agent Configuration
DASH_API_URL=${API_BASE_URL}
DASH_API_KEY=${api_key}
DASH_SERVER_ID=${server.id}
DASH_POLL_INTERVAL=${server.poll_interval}
DASH_COLLECT_DOCKER=true
DASH_COLLECT_PROCESSES=true
DASH_LOG_LEVEL=INFO
`;

  const handleCopy = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(api_key);
      } else {
        const ta = document.createElement('textarea');
        ta.value = api_key;
        ta.style.position = 'fixed'; ta.style.left = '-999999px';
        document.body.appendChild(ta); ta.focus(); ta.select();
        document.execCommand('copy'); ta.remove();
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { alert('Failed to copy. Please copy manually.'); }
  };

  const handleDownload = () => {
    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `agent-${server.name}.env`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Server Created Successfully!</h3>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-4">
          <p className="text-sm text-yellow-800 dark:text-yellow-200 font-medium">
            ⚠️ Save this API key now — it will not be shown again!
          </p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Server ID</label>
            <div className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-md font-mono text-sm text-gray-900 dark:text-white">{server.id}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">API Key</label>
            <div className="flex gap-2">
              <div className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-md font-mono text-sm text-gray-900 dark:text-white break-all">{api_key}</div>
              <button onClick={handleCopy} className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 whitespace-nowrap">
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Agent Configuration File</label>
            <button onClick={handleDownload} className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download agent.env File
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Upload to <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">/etc/dash-agent/agent.env</code>
            </p>
          </div>
        </div>
        <button onClick={onClose} className="w-full mt-6 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">Done</button>
      </div>
    </div>
  );
}

function DeleteConfirmModal({ isOpen, onClose, server, onConfirm }) {
  const [deleting, setDeleting] = useState(false);
  if (!isOpen || !server) return null;
  const handleDelete = async () => { setDeleting(true); await onConfirm(); setDeleting(false); };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Delete Server?</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Delete <strong>{server.name}</strong>? This removes all associated metrics and monitoring data.
        </p>
        <div className="flex gap-2">
          <button onClick={onClose} disabled={deleting} className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50">Cancel</button>
          <button onClick={handleDelete} disabled={deleting} className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50">
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Sparkline (tiny inline chart) ───────────────────────────────────────────

function Sparkline({ data, dataKey, color }) {
  if (!data || data.length < 2) return null;
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={1.5} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ─── Metric Card ──────────────────────────────────────────────────────────────

function MetricCard({ label, value, unit, pct, sparkData, sparkKey, sparkColor }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</span>
        <span className={`text-2xl font-bold ${metricColor(pct)}`}>
          {value != null ? value : '—'}{unit && value != null ? unit : ''}
        </span>
      </div>
      {pct != null && (
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
          <div className={`h-1.5 rounded-full ${metricBarColor(pct)}`} style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
      )}
      {sparkData && <Sparkline data={sparkData} dataKey={sparkKey} color={sparkColor} />}
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab({ server, detail, tempUnit }) {
  const latest = detail?.recent_metrics?.[0];
  // recent_metrics is ordered desc from backend, reverse for sparkline (oldest→newest)
  const sparkData = detail?.recent_metrics ? [...detail.recent_metrics].reverse() : [];

  return (
    <div className="space-y-6">
      {/* Status bar */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${server.is_online ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className={`font-semibold ${server.is_online ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {server.is_online ? 'Online' : 'Offline'}
          </span>
        </div>
        {server.hostname && <span className="text-sm text-gray-500 dark:text-gray-400">Host: <span className="font-mono text-gray-700 dark:text-gray-300">{server.hostname}</span></span>}
        {server.ip_address && <span className="text-sm text-gray-500 dark:text-gray-400">IP: <span className="font-mono text-gray-700 dark:text-gray-300">{server.ip_address}</span></span>}
        {server.last_seen && <span className="text-sm text-gray-500 dark:text-gray-400">Last seen: <span className="text-gray-700 dark:text-gray-300">{formatRelativeTime(server.last_seen)}</span></span>}
        <span className="text-sm text-gray-500 dark:text-gray-400">Poll: <span className="text-gray-700 dark:text-gray-300">{server.poll_interval}s</span></span>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="CPU" value={latest?.cpu_percent?.toFixed(1)} unit="%" pct={latest?.cpu_percent} sparkData={sparkData} sparkKey="cpu_percent" sparkColor="#3b82f6" />
        <MetricCard label="Memory" value={latest?.memory_percent?.toFixed(1)} unit="%" pct={latest?.memory_percent} sparkData={sparkData} sparkKey="memory_percent" sparkColor="#8b5cf6" />
        <MetricCard label="Disk" value={latest?.disk_percent?.toFixed(1)} unit="%" pct={latest?.disk_percent} sparkData={sparkData} sparkKey="disk_percent" sparkColor="#f59e0b" />
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 flex flex-col gap-2">
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Network</span>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-sm">
              <span className="text-blue-500">↓</span>
              <span className="font-mono text-gray-700 dark:text-gray-300">{formatBytes(latest?.network_in)}</span>
              <span className="text-xs text-gray-400">recv</span>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <span className="text-green-500">↑</span>
              <span className="font-mono text-gray-700 dark:text-gray-300">{formatBytes(latest?.network_out)}</span>
              <span className="text-xs text-gray-400">sent</span>
            </div>
          </div>
        </div>
      </div>

      {/* Temperature sensors */}
      {(() => {
        const latestTemps = detail?.recent_metrics?.[0]?.temperatures;
        if (!latestTemps || Object.keys(latestTemps).length === 0) return null;
        return (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Temperatures</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(latestTemps).map(([sensor, celsius]) => (
                <div key={sensor} className={`rounded-lg p-3 flex items-center justify-between ${tempBg(celsius)}`}>
                  <div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">{sensor}</div>
                    <div className={`text-xl font-bold ${tempColor(celsius)}`}>
                      {formatTemp(celsius, tempUnit)}
                    </div>
                  </div>
                  <div className="text-2xl opacity-60">{tempEmoji(celsius)}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Processes summary */}
      {detail?.processes?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Monitored Processes</h3>
          <div className="flex flex-wrap gap-2">
            {detail.processes.map((p) => (
              <span key={p.id} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${p.is_running ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${p.is_running ? 'bg-green-500' : 'bg-red-500'}`} />
                {p.process_name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Drives summary */}
      {detail?.drives?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Drives</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {detail.drives.map((d) => (
              <div key={d.id} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-sm text-gray-700 dark:text-gray-300">{d.mount_point}</span>
                  <span className={`text-sm font-medium ${metricColor(d.percent_used)}`}>
                    {d.percent_used != null ? `${d.percent_used.toFixed(0)}%` : '—'}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${metricBarColor(d.percent_used)}`} style={{ width: `${Math.min(d.percent_used ?? 0, 100)}%` }} />
                </div>
                <div className="text-xs text-gray-400 mt-1">{formatBytes(d.used_bytes)} / {formatBytes(d.total_bytes)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Docker summary */}
      {detail?.containers?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Docker Containers</h3>
          <div className="flex flex-wrap gap-2">
            {detail.containers.map((c) => (
              <span key={c.id} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.status === 'running' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${c.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`} />
                {c.name || c.container_id.slice(0, 12)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Metrics Tab ──────────────────────────────────────────────────────────────

const CHART_TOOLTIP_STYLE = {
  contentStyle: { backgroundColor: 'rgba(17,24,39,0.9)', border: '1px solid #374151', borderRadius: '8px', color: '#f9fafb', fontSize: '12px' },
};

function MetricsTab({ serverId, tempUnit }) {
  const [hours, setHours] = useState(1);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/servers/${serverId}/metrics?hours=${hours}`);
      setData(res.data.map((m) => ({
        ...m,
        time: new Date(m.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        network_in_mb: m.network_in != null ? +(m.network_in / 1024 / 1024).toFixed(1) : null,
        network_out_mb: m.network_out != null ? +(m.network_out / 1024 / 1024).toFixed(1) : null,
      })));
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [serverId, hours]);

  useEffect(() => { fetchMetrics(); }, [fetchMetrics]);

  const timeRanges = [{ label: '1h', value: 1 }, { label: '6h', value: 6 }, { label: '24h', value: 24 }, { label: '7d', value: 168 }];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">Time range:</span>
        {timeRanges.map((r) => (
          <button key={r.value} onClick={() => setHours(r.value)}
            className={`px-3 py-1 text-sm rounded-md ${hours === r.value ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
            {r.label}
          </button>
        ))}
        <button onClick={fetchMetrics} className="ml-auto px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : data.length === 0 ? (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">No metrics in the selected time range</div>
      ) : (
        <>
          {/* CPU & Memory chart */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">CPU & Memory (%)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#9ca3af' }} width={38} />
                <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v, name) => [`${v?.toFixed(1)}%`, name === 'cpu_percent' ? 'CPU' : 'Memory']} />
                <Legend formatter={(v) => v === 'cpu_percent' ? 'CPU' : 'Memory'} wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="cpu_percent" stroke="#3b82f6" dot={false} strokeWidth={1.5} isAnimationActive={false} name="cpu_percent" />
                <Line type="monotone" dataKey="memory_percent" stroke="#8b5cf6" dot={false} strokeWidth={1.5} isAnimationActive={false} name="memory_percent" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Disk chart */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Disk Usage (%)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#9ca3af' }} width={38} />
                <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v) => [`${v?.toFixed(1)}%`, 'Disk']} />
                <Line type="monotone" dataKey="disk_percent" stroke="#f59e0b" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Network chart */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Network Total (MB)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis tickFormatter={(v) => `${v}M`} tick={{ fontSize: 11, fill: '#9ca3af' }} width={42} />
                <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v, name) => [`${v} MB`, name === 'network_in_mb' ? 'Received' : 'Sent']} />
                <Legend formatter={(v) => v === 'network_in_mb' ? 'Received' : 'Sent'} wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="network_in_mb" stroke="#06b6d4" dot={false} strokeWidth={1.5} isAnimationActive={false} name="network_in_mb" />
                <Line type="monotone" dataKey="network_out_mb" stroke="#10b981" dot={false} strokeWidth={1.5} isAnimationActive={false} name="network_out_mb" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Temperature chart — only rendered if any data point has temps */}
          {(() => {
            // Collect all unique sensor names across all data points
            const sensorNames = new Set();
            data.forEach((d) => {
              if (d.temperatures) Object.keys(d.temperatures).forEach((k) => sensorNames.add(k));
            });
            if (sensorNames.size === 0) return null;

            // Flatten temps into chart data, converting to display unit
            const tempData = data.map((d) => ({
              time: d.time,
              ...Object.fromEntries(
                [...sensorNames].map((name) => {
                  const c = d.temperatures?.[name] ?? null;
                  return [name, c != null ? (tempUnit === 'F' ? +(toF(c).toFixed(1)) : +c.toFixed(1)) : null];
                })
              ),
            }));

            const SENSOR_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6'];

            return (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Temperatures (°{tempUnit})</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={tempData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                    <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                    <YAxis tickFormatter={(v) => `${v}°`} tick={{ fontSize: 11, fill: '#9ca3af' }} width={36} domain={['auto', 'auto']} />
                    <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v, name) => [v != null ? `${v.toFixed(1)}°${tempUnit}` : '—', name]} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    {[...sensorNames].map((name, i) => (
                      <Line key={name} type="monotone" dataKey={name} stroke={SENSOR_COLORS[i % SENSOR_COLORS.length]}
                        dot={false} strokeWidth={1.5} isAnimationActive={false} connectNulls />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            );
          })()}
        </>
      )}
    </div>
  );
}

// ─── Processes Tab ────────────────────────────────────────────────────────────

function AddProcessModal({ isOpen, onClose, onAdd }) {
  const [processName, setProcessName] = useState('');
  const [matchPattern, setMatchPattern] = useState('');
  const [hint, setHint] = useState('');
  const [category, setCategory] = useState('Custom');
  const [submitting, setSubmitting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [presets, setPresets] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    api.get('/servers/process-presets').then((r) => setPresets(r.data)).catch(() => {});
  }, [isOpen]);

  // Group presets by category
  const grouped = presets.reduce((acc, p) => {
    (acc[p.category] = acc[p.category] || []).push(p);
    return acc;
  }, {});

  const handlePreset = (preset) => {
    setProcessName(preset.name);
    setMatchPattern(preset.pattern);
    setHint(preset.hint || '');
    setCategory(preset.category);
    setSelectedPresetId(preset.id);
  };

  const handleSavePreset = async () => {
    if (!processName.trim() || !matchPattern.trim()) return;
    setSaving(true);
    try {
      const res = await api.post('/servers/process-presets', {
        category: category.trim() || 'Custom',
        name: processName.trim(),
        pattern: matchPattern.trim(),
        hint: hint.trim() || null,
        sort_order: 0,
      });
      setPresets((prev) => [...prev, res.data]);
      setSelectedPresetId(res.data.id);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save preset');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePreset = async (preset) => {
    setDeletingId(preset.id);
    try {
      await api.delete(`/servers/process-presets/${preset.id}`);
      setPresets((prev) => prev.filter((p) => p.id !== preset.id));
      if (selectedPresetId === preset.id) setSelectedPresetId(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete preset');
    } finally {
      setDeletingId(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!processName.trim() || !matchPattern.trim()) return;
    setSubmitting(true);
    await onAdd({ process_name: processName.trim(), match_pattern: matchPattern.trim() });
    setProcessName(''); setMatchPattern(''); setHint(''); setCategory('Custom'); setSelectedPresetId(null);
    setSubmitting(false);
    onClose();
  };

  const isCurrentPresetSaved = selectedPresetId != null;

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Monitor Process</h3>

        {/* Preset picker */}
        <div className="mb-4 overflow-y-auto max-h-52 border border-gray-200 dark:border-gray-700 rounded-md flex-shrink-0">
          {Object.keys(grouped).length === 0 ? (
            <div className="px-3 py-4 text-xs text-gray-400 text-center">Loading presets...</div>
          ) : (
            Object.entries(grouped).map(([cat, items]) => (
              <div key={cat}>
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/60 sticky top-0">
                  {cat}
                </div>
                {items.map((item) => (
                  <div key={item.id}
                    className={`flex items-center group hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors ${selectedPresetId === item.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}>
                    <button type="button" onClick={() => handlePreset(item)} className="flex-1 text-left px-3 py-2 min-w-0">
                      <div className="text-sm font-medium text-gray-800 dark:text-gray-200">{item.name}</div>
                      {item.hint && <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{item.hint}</div>}
                    </button>
                    {!item.is_builtin && (
                      <button type="button" onClick={() => handleDeletePreset(item)} disabled={deletingId === item.id}
                        className="px-2 py-1 mr-1 text-xs text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                        title="Remove preset">
                        {deletingId === item.id ? '…' : '✕'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Display Name</label>
            <input type="text" value={processName}
              onChange={(e) => { setProcessName(e.target.value); setSelectedPresetId(null); }}
              placeholder="nginx" required disabled={submitting}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Match Pattern</label>
            <input type="text" value={matchPattern}
              onChange={(e) => { setMatchPattern(e.target.value); setSelectedPresetId(null); }}
              placeholder="nginx" required disabled={submitting}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {hint || 'Matched against process name and command line'}
            </p>
          </div>

          {/* Save as preset — shown when fields are filled and not already a saved preset */}
          {processName.trim() && matchPattern.trim() && !isCurrentPresetSaved && (
            <div className="flex items-center gap-2 pt-1">
              <input type="text" value={category} onChange={(e) => setCategory(e.target.value)}
                placeholder="Category (e.g. My App)"
                className="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
              <button type="button" onClick={handleSavePreset} disabled={saving}
                className="px-3 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 border border-blue-300 dark:border-blue-700 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:opacity-50 whitespace-nowrap">
                {saving ? 'Saving…' : '+ Save as preset'}
              </button>
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose} disabled={submitting}
              className="flex-1 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50">
              Cancel
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
              {submitting ? 'Adding...' : 'Add Process'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ProcessesTab({ serverId, processes, onRefresh }) {
  const [showAdd, setShowAdd] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const handleAdd = async (processData) => {
    try {
      await api.post(`/servers/${serverId}/processes`, processData);
      onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add process');
    }
  };

  const handleDelete = async (processId) => {
    setDeleting(processId);
    try {
      await api.delete(`/servers/${serverId}/processes/${processId}`);
      onRefresh();
    } catch (err) {
      alert('Failed to remove process');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">{processes.length} monitored {processes.length === 1 ? 'process' : 'processes'}</span>
        <button onClick={() => setShowAdd(true)} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          Add Process
        </button>
      </div>

      {processes.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <p>No processes monitored yet.</p>
          <p className="text-sm mt-1">Add a process to track its running status and resource usage.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Name</th>
                <th className="pb-2 pr-4">Pattern</th>
                <th className="pb-2 pr-4">CPU</th>
                <th className="pb-2 pr-4">Memory</th>
                <th className="pb-2 pr-4">PID</th>
                <th className="pb-2 pr-4">Updated</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {processes.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="py-3 pr-4">
                    <div className={`flex items-center gap-1.5 ${p.is_running ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      <div className={`w-2 h-2 rounded-full ${p.is_running ? 'bg-green-500' : 'bg-red-500'}`} />
                      {p.is_running ? 'Running' : 'Stopped'}
                    </div>
                  </td>
                  <td className="py-3 pr-4 font-medium text-gray-900 dark:text-white">{p.process_name}</td>
                  <td className="py-3 pr-4 font-mono text-gray-500 dark:text-gray-400">{p.match_pattern}</td>
                  <td className="py-3 pr-4 text-gray-700 dark:text-gray-300">{p.cpu_percent != null ? `${p.cpu_percent.toFixed(1)}%` : '—'}</td>
                  <td className="py-3 pr-4 text-gray-700 dark:text-gray-300">{p.memory_mb != null ? `${p.memory_mb} MB` : '—'}</td>
                  <td className="py-3 pr-4 font-mono text-gray-500 dark:text-gray-400">{p.pid ?? '—'}</td>
                  <td className="py-3 pr-4 text-gray-400 text-xs">{formatRelativeTime(p.updated_at)}</td>
                  <td className="py-3">
                    <button onClick={() => handleDelete(p.id)} disabled={deleting === p.id}
                      className="text-red-500 hover:text-red-700 dark:hover:text-red-400 disabled:opacity-50 text-xs">
                      {deleting === p.id ? '...' : 'Remove'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AddProcessModal isOpen={showAdd} onClose={() => setShowAdd(false)} onAdd={handleAdd} />
    </div>
  );
}

// ─── Drives Tab ───────────────────────────────────────────────────────────────

function AddDriveModal({ isOpen, onClose, onAdd }) {
  const [mountPoint, setMountPoint] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!mountPoint.trim()) return;
    setSubmitting(true);
    await onAdd({ mount_point: mountPoint.trim() });
    setMountPoint('');
    setSubmitting(false);
    onClose();
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Monitor Drive</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mount Point</label>
            <input type="text" value={mountPoint} onChange={(e) => setMountPoint(e.target.value)} placeholder="/mnt/data" required disabled={submitting}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Must start with /</p>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} disabled={submitting} className="flex-1 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50">Cancel</button>
            <button type="submit" disabled={submitting} className="flex-1 px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Adding...' : 'Add Drive'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DrivesTab({ serverId, drives, onRefresh }) {
  const [showAdd, setShowAdd] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const handleAdd = async (driveData) => {
    try {
      await api.post(`/servers/${serverId}/drives`, driveData);
      onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add drive');
    }
  };

  const handleDelete = async (driveId) => {
    setDeleting(driveId);
    try {
      await api.delete(`/servers/${serverId}/drives/${driveId}`);
      onRefresh();
    } catch {
      alert('Failed to remove drive');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">{drives.length} monitored {drives.length === 1 ? 'drive' : 'drives'}</span>
        <button onClick={() => setShowAdd(true)} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          Add Drive
        </button>
      </div>

      {drives.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <p>No drives monitored yet.</p>
          <p className="text-sm mt-1">Add a mount point to track disk capacity.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {drives.map((d) => (
            <div key={d.id} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-mono font-medium text-gray-900 dark:text-white">{d.mount_point}</div>
                  {d.device && <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{d.device} {d.fstype ? `(${d.fstype})` : ''}</div>}
                </div>
                <div className="flex items-center gap-2">
                  {!d.is_mounted && <span className="text-xs text-red-500 bg-red-100 dark:bg-red-900/30 px-2 py-0.5 rounded">Unmounted</span>}
                  {d.is_readonly && <span className="text-xs text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 px-2 py-0.5 rounded">Read-only</span>}
                  <button onClick={() => handleDelete(d.id)} disabled={deleting === d.id}
                    className="text-red-500 hover:text-red-700 text-xs disabled:opacity-50">
                    {deleting === d.id ? '...' : 'Remove'}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-500 dark:text-gray-400">{formatBytes(d.used_bytes)} used of {formatBytes(d.total_bytes)}</span>
                <span className={`font-medium ${metricColor(d.percent_used)}`}>{d.percent_used != null ? `${d.percent_used.toFixed(1)}%` : '—'}</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div className={`h-2 rounded-full ${metricBarColor(d.percent_used)}`} style={{ width: `${Math.min(d.percent_used ?? 0, 100)}%` }} />
              </div>
              <div className="text-xs text-gray-400 mt-1">{formatBytes(d.free_bytes)} free</div>
              <div className="text-xs text-gray-400 mt-1">Updated {formatRelativeTime(d.updated_at)}</div>
            </div>
          ))}
        </div>
      )}

      <AddDriveModal isOpen={showAdd} onClose={() => setShowAdd(false)} onAdd={handleAdd} />
    </div>
  );
}

// ─── Docker Tab ───────────────────────────────────────────────────────────────

function DockerTab({ containers }) {
  if (containers.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400 dark:text-gray-500">
        <p>No Docker containers reported.</p>
        <p className="text-sm mt-1">Make sure the agent has Docker access and <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-xs">DASH_COLLECT_DOCKER=true</code> is set.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            <th className="pb-2 pr-4">Status</th>
            <th className="pb-2 pr-4">Name</th>
            <th className="pb-2 pr-4">Image</th>
            <th className="pb-2 pr-4">CPU</th>
            <th className="pb-2 pr-4">Memory</th>
            <th className="pb-2">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {containers.map((c) => (
            <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <td className="py-3 pr-4">
                <div className={`flex items-center gap-1.5 ${c.status === 'running' ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                  <div className={`w-2 h-2 rounded-full ${c.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`} />
                  {c.status ?? 'unknown'}
                </div>
              </td>
              <td className="py-3 pr-4 font-medium text-gray-900 dark:text-white">{c.name || '—'}</td>
              <td className="py-3 pr-4 font-mono text-xs text-gray-500 dark:text-gray-400 max-w-[200px] truncate">{c.image || '—'}</td>
              <td className="py-3 pr-4 text-gray-700 dark:text-gray-300">{c.cpu_percent != null ? `${c.cpu_percent.toFixed(1)}%` : '—'}</td>
              <td className="py-3 pr-4 text-gray-700 dark:text-gray-300">
                {c.memory_usage != null ? formatBytes(c.memory_usage) : '—'}
                {c.memory_limit ? ` / ${formatBytes(c.memory_limit)}` : ''}
              </td>
              <td className="py-3 text-gray-400 text-xs">{formatRelativeTime(c.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Setup Tab ────────────────────────────────────────────────────────────────

function SetupTab({ server, onDelete }) {
  // Backend URL for the agent — derived from the page's hostname (= the server's IP)
  const [backendUrl, setBackendUrl] = useState(() => {
    const { protocol, hostname } = window.location;
    // API_BASE_URL may be relative (/api/v1) in production; extract port from it if absolute
    const apiBase = API_BASE_URL;
    if (!apiBase.startsWith('/')) {
      try {
        const u = new URL(apiBase);
        return `${u.protocol}//${u.hostname}${u.port ? `:${u.port}` : ''}`;
      } catch { /* fall through */ }
    }
    // Default: same host as the browser, same port (goes through nginx)
    const port = window.location.port;
    return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
  });

  const agentApiUrl = backendUrl ? `${backendUrl.replace(/\/$/, '')}/api/v1` : '';

  const envContent = `DASH_API_URL=${agentApiUrl || '<http://YOUR-SERVER-IP:8000>/api/v1'}
DASH_API_KEY=<your-api-key>
DASH_SERVER_ID=${server.id}
DASH_POLL_INTERVAL=${server.poll_interval}
DASH_COLLECT_DOCKER=true
DASH_COLLECT_PROCESSES=true
DASH_LOG_LEVEL=INFO`;

  // SSH Deploy state
  const [sshForm, setSshForm] = useState({
    ssh_host: server.ip_address || server.hostname || '',
    ssh_port: 22,
    ssh_user: 'root',
    ssh_password: '',
    ssh_key: '',
    sudo_password: '',
    auth_method: 'password', // 'password' or 'key'
  });
  const [deploying, setDeploying] = useState(false);
  const [deployLog, setDeployLog] = useState(null);
  const [deploySuccess, setDeploySuccess] = useState(null);

  const handleDeploy = async (e) => {
    e.preventDefault();
    setDeploying(true);
    setDeployLog(null);
    setDeploySuccess(null);
    try {
      const payload = {
        ssh_host: sshForm.ssh_host,
        ssh_port: sshForm.ssh_port,
        ssh_user: sshForm.ssh_user,
        backend_url: agentApiUrl || undefined,
        ...(sshForm.auth_method === 'password'
          ? { ssh_password: sshForm.ssh_password }
          : { ssh_key: sshForm.ssh_key, ...(sshForm.sudo_password ? { sudo_password: sshForm.sudo_password } : {}) }),
      };
      const res = await api.post(`/servers/${server.id}/deploy`, payload);
      setDeployLog(res.data.log);
      setDeploySuccess(res.data.success);
    } catch (err) {
      setDeployLog([err.response?.data?.detail || 'Deployment request failed']);
      setDeploySuccess(false);
    } finally {
      setDeploying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Server Info */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Server Details</h3>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          {[
            ['ID', server.id],
            ['Name', server.name],
            ['Hostname', server.hostname || '—'],
            ['IP Address', server.ip_address || '—'],
            ['MAC Address', server.mac_address || '—'],
            ['Poll Interval', `${server.poll_interval}s`],
            ['Registered', formatTime(server.created_at)],
          ].map(([label, value]) => (
            <div key={label} className="flex flex-col">
              <dt className="text-gray-500 dark:text-gray-400">{label}</dt>
              <dd className="font-mono text-gray-700 dark:text-gray-300">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Manual config */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Manual Agent Configuration</h3>
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Backend URL <span className="text-gray-400">(full URL reachable from the remote server)</span>
          </label>
          <div className="flex gap-2 items-center">
            <input
              type="url"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              placeholder="http://192.168.1.100:8000"
              className="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
            />
            {!backendUrl && (
              <span className="text-xs text-yellow-600 dark:text-yellow-400 whitespace-nowrap">⚠ required</span>
            )}
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Place this in <code className="bg-gray-200 dark:bg-gray-600 px-1 rounded">/etc/dash-agent/agent.env</code> on your server:</p>
        <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-md overflow-x-auto font-mono leading-relaxed whitespace-pre">{envContent}</pre>
      </div>

      {/* SSH Deploy */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Deploy via SSH</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
          Automatically copy the agent script and configure systemd on the remote server. You'll still need to add the <code className="bg-gray-200 dark:bg-gray-600 px-1 rounded">DASH_API_KEY</code> manually after deployment.
        </p>

        <form onSubmit={handleDeploy} className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">SSH Host</label>
              <input type="text" value={sshForm.ssh_host} required
                onChange={(e) => setSshForm({ ...sshForm, ssh_host: e.target.value })}
                placeholder="192.168.1.100"
                className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Port</label>
              <input type="number" value={sshForm.ssh_port} min="1" max="65535"
                onChange={(e) => setSshForm({ ...sshForm, ssh_port: parseInt(e.target.value) })}
                className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">SSH User</label>
            <input type="text" value={sshForm.ssh_user} required
              onChange={(e) => setSshForm({ ...sshForm, ssh_user: e.target.value })}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>

          {/* Auth method toggle */}
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">Authentication</label>
            <div className="flex gap-2 mb-3">
              {['password', 'key'].map((method) => (
                <button key={method} type="button"
                  onClick={() => setSshForm({ ...sshForm, auth_method: method })}
                  className={`px-3 py-1 text-xs rounded-md ${sshForm.auth_method === method ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'}`}>
                  {method === 'password' ? 'Password' : 'Private Key'}
                </button>
              ))}
            </div>

            {sshForm.auth_method === 'password' ? (
              <input type="password" value={sshForm.ssh_password} required
                onChange={(e) => setSshForm({ ...sshForm, ssh_password: e.target.value })}
                placeholder="SSH password"
                className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            ) : (
              <>
                <textarea value={sshForm.ssh_key} required rows={6}
                  onChange={(e) => setSshForm({ ...sshForm, ssh_key: e.target.value })}
                  placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;..."
                  className="w-full px-3 py-1.5 text-xs font-mono border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                <div className="mt-2">
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                    Sudo password <span className="text-gray-400">(leave blank if passwordless sudo)</span>
                  </label>
                  <input type="password" value={sshForm.sudo_password}
                    onChange={(e) => setSshForm({ ...sshForm, sudo_password: e.target.value })}
                    placeholder="sudo password"
                    className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                </div>
              </>
            )}
          </div>

          <button type="submit" disabled={deploying}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2">
            {deploying ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Deploying...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Deploy Agent via SSH
              </>
            )}
          </button>
        </form>

        {/* Deploy log output */}
        {deployLog && (
          <div className="mt-4">
            <div className={`flex items-center gap-2 mb-2 text-sm font-medium ${deploySuccess ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {deploySuccess ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              )}
              {deploySuccess ? 'Deployment succeeded' : 'Deployment failed'}
            </div>
            <pre className="bg-gray-900 text-gray-300 text-xs p-3 rounded-md overflow-x-auto font-mono leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
              {deployLog.join('\n')}
            </pre>
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="border border-red-200 dark:border-red-800 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Danger Zone</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Deleting this server removes all metrics, process monitoring, and drive data permanently.</p>
        <button onClick={onDelete} className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700">
          Delete Server
        </button>
      </div>
    </div>
  );
}

// ─── Server Detail View ───────────────────────────────────────────────────────

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'metrics', label: 'Metrics' },
  { id: 'processes', label: 'Processes' },
  { id: 'drives', label: 'Drives' },
  { id: 'docker', label: 'Docker' },
  { id: 'setup', label: 'Setup' },
];

function ServerDetailView({ server, onDelete, onRefresh }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tempUnit, setTempUnit] = useState(() => localStorage.getItem('tempUnit') || 'F');

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/servers/${server.id}`);
      setDetail(res.data);
    } catch (err) {
      console.error('Failed to fetch server detail:', err);
    } finally {
      setLoading(false);
    }
  }, [server.id]);

  useEffect(() => { fetchDetail(); }, [fetchDetail]);

  // Auto-refresh every 60s on overview tab
  useEffect(() => {
    if (activeTab !== 'overview') return;
    const interval = setInterval(fetchDetail, 60000);
    return () => clearInterval(interval);
  }, [activeTab, fetchDetail]);

  const tabCounts = detail ? {
    processes: detail.processes.length,
    drives: detail.drives.length,
    docker: detail.containers.length,
  } : {};

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex items-center gap-1 border-b border-gray-200 dark:border-gray-700 mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {tab.label}
            {tabCounts[tab.id] != null && tabCounts[tab.id] > 0 && (
              <span className="ml-1.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-1.5 py-0.5 rounded-full">
                {tabCounts[tab.id]}
              </span>
            )}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-2">
          <div className="flex rounded-md overflow-hidden border border-gray-200 dark:border-gray-600 text-xs font-medium">
            {['F', 'C'].map((unit) => (
              <button key={unit} onClick={() => { setTempUnit(unit); localStorage.setItem('tempUnit', unit); }}
                className={`px-2.5 py-1 ${tempUnit === unit ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
                °{unit}
              </button>
            ))}
          </div>
          <button onClick={fetchDetail} className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" title="Refresh">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {loading && activeTab === 'overview' ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            {activeTab === 'overview' && <OverviewTab server={server} detail={detail} tempUnit={tempUnit} />}
            {activeTab === 'metrics' && <MetricsTab serverId={server.id} tempUnit={tempUnit} />}
            {activeTab === 'processes' && <ProcessesTab serverId={server.id} processes={detail?.processes ?? []} onRefresh={fetchDetail} />}
            {activeTab === 'drives' && <DrivesTab serverId={server.id} drives={detail?.drives ?? []} onRefresh={fetchDetail} />}
            {activeTab === 'docker' && <DockerTab containers={detail?.containers ?? []} />}
            {activeTab === 'setup' && <SetupTab server={server} onDelete={onDelete} />}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Router Components ────────────────────────────────────────────────────────

function AddRouterModal({ isOpen, onClose, onSuccess }) {
  const [form, setForm] = useState({
    name: '', hostname: '', ssh_port: 22, ssh_user: 'root',
    ssh_password: '', ssh_key: '', auth_method: 'password',
    poll_interval: 60, script: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.hostname.trim()) { setError('Name and hostname are required'); return; }
    setSubmitting(true); setError(null);
    try {
      const payload = {
        name: form.name, hostname: form.hostname,
        ssh_port: form.ssh_port, ssh_user: form.ssh_user,
        poll_interval: form.poll_interval,
        script: form.script || null,
        ...(form.auth_method === 'password' ? { ssh_password: form.ssh_password } : { ssh_key: form.ssh_key }),
      };
      const res = await api.post('/routers', payload);
      onSuccess(res.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add router');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Add Router</h3>
        {error && <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
              <input type="text" value={form.name} required disabled={submitting}
                onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="office-router"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Hostname / IP *</label>
              <input type="text" value={form.hostname} required disabled={submitting}
                onChange={(e) => setForm({ ...form, hostname: e.target.value })} placeholder="192.168.1.1"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">SSH User</label>
              <input type="text" value={form.ssh_user} disabled={submitting}
                onChange={(e) => setForm({ ...form, ssh_user: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">SSH Port</label>
              <input type="number" value={form.ssh_port} min="1" max="65535" disabled={submitting}
                onChange={(e) => setForm({ ...form, ssh_port: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Poll Interval (s)</label>
              <input type="number" value={form.poll_interval} min="10" max="3600" disabled={submitting}
                onChange={(e) => setForm({ ...form, poll_interval: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Authentication</label>
            <div className="flex gap-2 mb-2">
              {['password', 'key'].map((m) => (
                <button key={m} type="button" onClick={() => setForm({ ...form, auth_method: m })}
                  className={`px-3 py-1 text-xs rounded-md ${form.auth_method === m ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300'}`}>
                  {m === 'password' ? 'Password' : 'Private Key'}
                </button>
              ))}
            </div>
            {form.auth_method === 'password' ? (
              <input type="password" value={form.ssh_password} disabled={submitting}
                onChange={(e) => setForm({ ...form, ssh_password: e.target.value })} placeholder="SSH password"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm" />
            ) : (
              <textarea value={form.ssh_key} rows={5} disabled={submitting}
                onChange={(e) => setForm({ ...form, ssh_key: e.target.value })} placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs font-mono" />
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Shell Script <span className="text-gray-400 font-normal">(optional — runs via SSH each poll)</span>
            </label>
            <textarea value={form.script} rows={4} disabled={submitting}
              onChange={(e) => setForm({ ...form, script: e.target.value })}
              placeholder={'cat /proc/loadavg\ncat /proc/meminfo | grep -E "MemTotal|MemFree"\nip -s link show br-lan'}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs font-mono" />
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} disabled={submitting}
              className="flex-1 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50">Cancel</button>
            <button type="submit" disabled={submitting}
              className="flex-1 px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Adding...' : 'Add Router'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RouterDetailView({ router, onDelete, onRefresh }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/routers/${router.id}/history`);
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch router history:', err);
    } finally {
      setLoading(false);
    }
  }, [router.id]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  useEffect(() => {
    const interval = setInterval(() => { fetchHistory(); onRefresh(); }, router.poll_interval * 1000);
    return () => clearInterval(interval);
  }, [fetchHistory, onRefresh, router.poll_interval]);

  const handlePollNow = async () => {
    setPolling(true);
    try {
      await api.post(`/routers/${router.id}/poll`);
      await fetchHistory();
      await onRefresh();
    } catch (err) {
      alert(err.response?.data?.detail || 'Poll failed');
    } finally {
      setPolling(false);
    }
  };

  const latest = history[0];

  return (
    <div className="space-y-6">
      {/* Status bar */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${router.is_online ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className={`font-semibold ${router.is_online ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {router.is_online ? 'Online' : 'Offline'}
          </span>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Host: <span className="font-mono text-gray-700 dark:text-gray-300">{router.hostname}</span>
        </span>
        {router.ping_ms != null && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Ping: <span className="font-mono text-gray-700 dark:text-gray-300">{router.ping_ms} ms</span>
          </span>
        )}
        {router.last_seen && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Last seen: <span className="text-gray-700 dark:text-gray-300">{formatRelativeTime(router.last_seen)}</span>
          </span>
        )}
        <span className="text-sm text-gray-500 dark:text-gray-400">Poll: {router.poll_interval}s</span>
        <button onClick={handlePollNow} disabled={polling}
          className="ml-auto px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1">
          {polling ? <><div className="animate-spin rounded-full h-3 w-3 border-b border-white" />Polling...</> : 'Poll Now'}
        </button>
      </div>

      {/* Latest script output */}
      {router.script && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Latest Output</h3>
            {latest && <span className="text-xs text-gray-400">{formatRelativeTime(latest.recorded_at)}</span>}
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            </div>
          ) : latest?.script_output ? (
            <pre className="bg-gray-900 text-green-400 text-xs p-4 rounded-md overflow-x-auto font-mono leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
              {latest.script_output}
            </pre>
          ) : (
            <div className="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">
              {latest?.is_online === false ? 'Router offline — no output' : 'No output yet'}
            </div>
          )}
        </div>
      )}

      {/* Ping history */}
      {history.length > 1 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Ping History</h3>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <ResponsiveContainer width="100%" height={120}>
              <LineChart
                data={[...history].reverse().map((h) => ({
                  time: new Date(h.recorded_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  ping_ms: h.is_online ? h.ping_ms : null,
                }))}
                margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis tickFormatter={(v) => `${v}ms`} tick={{ fontSize: 11, fill: '#9ca3af' }} width={42} />
                <Tooltip {...CHART_TOOLTIP_STYLE} formatter={(v) => [v != null ? `${v} ms` : 'offline', 'Ping']} />
                <Line type="monotone" dataKey="ping_ms" stroke="#3b82f6" dot={false} strokeWidth={1.5} isAnimationActive={false} connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Poll history table */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Poll History</h3>
        {history.length === 0 ? (
          <div className="text-sm text-gray-400 text-center py-8">No poll results yet — waiting for first poll</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <th className="pb-2 pr-4">Time</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Ping</th>
                  <th className="pb-2">Output preview</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {history.map((h) => (
                  <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="py-2 pr-4 text-xs text-gray-400">{formatRelativeTime(h.recorded_at)}</td>
                    <td className="py-2 pr-4">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${h.is_online ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${h.is_online ? 'bg-green-500' : 'bg-red-500'}`} />
                        {h.is_online ? 'Online' : 'Offline'}
                      </span>
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-gray-600 dark:text-gray-300">
                      {h.ping_ms != null ? `${h.ping_ms} ms` : '—'}
                    </td>
                    <td className="py-2 text-xs text-gray-400 font-mono truncate max-w-xs">
                      {h.script_output ? h.script_output.split('\n')[0].slice(0, 80) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Setup / script editor */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Configuration</h3>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          {[
            ['Host', router.hostname],
            ['SSH User', router.ssh_user],
            ['SSH Port', router.ssh_port],
            ['Auth', router.has_key ? 'Private key' : router.has_password ? 'Password' : 'None'],
            ['Poll Interval', `${router.poll_interval}s`],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-gray-500 dark:text-gray-400 text-xs">{label}</dt>
              <dd className="font-mono text-gray-700 dark:text-gray-300">{value}</dd>
            </div>
          ))}
        </dl>
        {router.script && (
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Script</div>
            <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-md font-mono whitespace-pre-wrap">{router.script}</pre>
          </div>
        )}
        <div className="pt-2 border-t border-red-200 dark:border-red-800">
          <button onClick={onDelete} className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700">
            Delete Router
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ServersPage() {
  const { user, logout } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();

  // Servers state
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [newServerData, setNewServerData] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Routers state
  const [routers, setRouters] = useState([]);
  const [selectedRouterId, setSelectedRouterId] = useState(null);
  const [showAddRouterModal, setShowAddRouterModal] = useState(false);
  const [deleteRouterTarget, setDeleteRouterTarget] = useState(null);

  // 'server' | 'router'
  const [selectionType, setSelectionType] = useState('server');

  const fetchServers = useCallback(async () => {
    try {
      const res = await api.get('/servers');
      setServers(res.data);
      if (!selectedId && res.data.length > 0 && selectionType === 'server') setSelectedId(res.data[0].id);
    } catch (err) {
      console.error('Failed to fetch servers:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedId, selectionType]);

  const fetchRouters = useCallback(async () => {
    try {
      const res = await api.get('/routers');
      setRouters(res.data);
    } catch (err) {
      console.error('Failed to fetch routers:', err);
    }
  }, []);

  useEffect(() => { fetchServers(); fetchRouters(); }, []);

  useEffect(() => {
    const interval = setInterval(() => { fetchServers(); fetchRouters(); }, 60000);
    return () => clearInterval(interval);
  }, [fetchServers, fetchRouters]);

  const handleAddSuccess = (serverData) => {
    setNewServerData(serverData);
    setShowApiKeyModal(true);
    fetchServers();
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/servers/${deleteTarget.id}`);
      setDeleteTarget(null);
      if (selectedId === deleteTarget.id) setSelectedId(null);
      fetchServers();
    } catch {
      alert('Failed to delete server');
    }
  };

  const handleDeleteRouterConfirm = async () => {
    if (!deleteRouterTarget) return;
    try {
      await api.delete(`/routers/${deleteRouterTarget.id}`);
      setDeleteRouterTarget(null);
      if (selectedRouterId === deleteRouterTarget.id) setSelectedRouterId(null);
      fetchRouters();
    } catch {
      alert('Failed to delete router');
    }
  };

  const selectServer = (id) => { setSelectedId(id); setSelectionType('server'); setSelectedRouterId(null); };
  const selectRouter = (id) => { setSelectedRouterId(id); setSelectionType('router'); setSelectedId(null); };

  const selectedServer = servers.find((s) => s.id === selectedId);
  const selectedRouter = routers.find((r) => r.id === selectedRouterId);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow sticky top-0 z-40">
        <div className="max-w-full px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
              Personal Dash
            </Link>
            <span className="text-gray-300 dark:text-gray-600">/</span>
            <h1 className="text-lg font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              Server Monitor
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={toggleDarkMode} className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
              title={darkMode ? 'Light mode' : 'Dark mode'}>
              {darkMode ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
              )}
            </button>
            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200 dark:border-gray-700">
              <span className="text-sm text-gray-600 dark:text-gray-400 hidden sm:inline">{user?.display_name || user?.email}</span>
              <button onClick={logout} className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md" title="Logout">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Layout: sidebar + main */}
      <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 57px)' }}>

        {/* Sidebar */}
        <aside className="w-60 flex-shrink-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-y-auto">

          {/* Servers section */}
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <button onClick={() => setShowAddModal(true)}
              className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center justify-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Add Server
            </button>
          </div>

          <div className="p-2">
            <div className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Servers</div>
            {loading ? (
              <div className="flex items-center justify-center py-6">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
              </div>
            ) : servers.length === 0 ? (
              <div className="text-center py-4 text-xs text-gray-400 dark:text-gray-500">No servers yet</div>
            ) : (
              <ul className="space-y-0.5">
                {servers.map((server) => (
                  <li key={server.id}>
                    <button onClick={() => selectServer(server.id)}
                      className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center gap-2.5 ${
                        selectionType === 'server' && selectedId === server.id
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}>
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${server.is_online ? 'bg-green-500' : 'bg-red-400'}`} />
                      <div className="min-w-0">
                        <div className="font-medium text-sm truncate">{server.name}</div>
                        {server.hostname && <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{server.hostname}</div>}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Routers section */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700">
            <button onClick={() => setShowAddRouterModal(true)}
              className="w-full px-3 py-2 text-sm bg-gray-700 dark:bg-gray-600 text-white rounded-md hover:bg-gray-600 dark:hover:bg-gray-500 flex items-center justify-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Add Router
            </button>
          </div>

          <div className="p-2 pb-4">
            <div className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Routers</div>
            {routers.length === 0 ? (
              <div className="text-center py-4 text-xs text-gray-400 dark:text-gray-500">No routers yet</div>
            ) : (
              <ul className="space-y-0.5">
                {routers.map((r) => (
                  <li key={r.id}>
                    <button onClick={() => selectRouter(r.id)}
                      className={`w-full text-left px-3 py-2 rounded-md transition-colors flex items-center gap-2.5 ${
                        selectionType === 'router' && selectedRouterId === r.id
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}>
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${r.is_online ? 'bg-green-500' : 'bg-red-400'}`} />
                      <div className="min-w-0">
                        <div className="font-medium text-sm truncate">{r.name}</div>
                        <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{r.hostname}</div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          {selectionType === 'router' && selectedRouter ? (
            <div className="max-w-5xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mb-1 uppercase tracking-wider">Router</div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedRouter.name}</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{selectedRouter.hostname}</p>
                </div>
              </div>
              <RouterDetailView
                key={selectedRouter.id}
                router={selectedRouter}
                onDelete={() => setDeleteRouterTarget(selectedRouter)}
                onRefresh={fetchRouters}
              />
            </div>
          ) : selectionType === 'server' && selectedServer ? (
            <div className="max-w-5xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedServer.name}</h2>
                  {selectedServer.ip_address && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{selectedServer.ip_address}</p>
                  )}
                </div>
              </div>
              <ServerDetailView
                key={selectedServer.id}
                server={selectedServer}
                onDelete={() => setDeleteTarget(selectedServer)}
                onRefresh={fetchServers}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <svg className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              <p className="text-sm text-gray-500 dark:text-gray-400">Select a server or router from the sidebar</p>
            </div>
          )}
        </main>
      </div>

      {/* Modals */}
      <AddServerModal isOpen={showAddModal} onClose={() => setShowAddModal(false)} onSuccess={handleAddSuccess} />
      <ApiKeyModal isOpen={showApiKeyModal} onClose={() => { setShowApiKeyModal(false); setNewServerData(null); }} serverData={newServerData} />
      <DeleteConfirmModal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} server={deleteTarget} onConfirm={handleDeleteConfirm} />
      <AddRouterModal isOpen={showAddRouterModal} onClose={() => setShowAddRouterModal(false)} onSuccess={(r) => { fetchRouters(); selectRouter(r.id); }} />
      <DeleteConfirmModal isOpen={!!deleteRouterTarget} onClose={() => setDeleteRouterTarget(null)} server={deleteRouterTarget} onConfirm={handleDeleteRouterConfirm} />
    </div>
  );
}
