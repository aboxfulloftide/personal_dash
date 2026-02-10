import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../../services/api';

function StatusBadge({ status }) {
  const statusConfig = {
    online: {
      color: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200',
      icon: '✓',
      label: 'Online',
    },
    degraded: {
      color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200',
      icon: '⚠',
      label: 'Degraded',
    },
    offline: {
      color: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200',
      icon: '✗',
      label: 'Offline',
    },
  };

  const config = statusConfig[status] || statusConfig.offline;

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium ${config.color}`}
    >
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </span>
  );
}

function PingResultItem({ result }) {
  const isReachable = result.is_reachable;

  return (
    <div
      className={`flex items-center justify-between py-2 px-2 rounded ${
        isReachable
          ? 'bg-green-50 dark:bg-green-900/10'
          : 'bg-red-50 dark:bg-red-900/10'
      }`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isReachable ? 'bg-green-500' : 'bg-red-500'
          }`}
        ></span>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {result.target_name}
        </span>
      </div>

      {isReachable ? (
        <div className="flex gap-3 text-xs text-gray-600 dark:text-gray-400">
          {result.latency_ms !== null && (
            <span>{result.latency_ms}ms</span>
          )}
          {result.jitter_ms !== null && (
            <span className="text-gray-500">±{result.jitter_ms}ms</span>
          )}
          {result.packet_loss_pct !== null && result.packet_loss_pct > 0 && (
            <span className="text-yellow-600 dark:text-yellow-400">
              {result.packet_loss_pct}% loss
            </span>
          )}
        </div>
      ) : (
        <span className="text-xs text-red-600 dark:text-red-400">
          Unreachable
        </span>
      )}
    </div>
  );
}

export default function NetworkStatusWidget({ config }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  // Get ping targets from config or use defaults
  const pingTargets = config.ping_targets || [
    { host: '8.8.8.8', name: 'Google DNS' },
    { host: '1.1.1.1', name: 'Cloudflare DNS' },
    { host: '208.67.222.222', name: 'OpenDNS' },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading((prev) => prev || data === null);
      setError(null);

      const response = await api.post('/network/status', { targets: pingTargets });

      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch network status');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(pingTargets)]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh interval
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    const refreshInterval = config.refresh_interval || 60;
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval * 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, config.refresh_interval]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500 p-4">
        <span className="text-2xl mb-2">🌐</span>
        <p className="text-sm text-center">{error}</p>
      </div>
    );
  }

  if (!data || !data.status) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <span className="text-4xl mb-2">🌐</span>
        <p className="text-sm">No network data</p>
      </div>
    );
  }

  const { status, ping_results } = data;

  return (
    <div className="space-y-3">
      {/* Connection Status Header */}
      <div className="flex items-center justify-between">
        <div>
          <StatusBadge status={status.status} />
        </div>
        {status.ip_address && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {status.ip_address}
          </div>
        )}
      </div>

      {/* ISP Info */}
      {(status.isp || status.location) && (
        <div className="text-xs text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700 pt-2">
          {status.isp && <div>{status.isp}</div>}
          {status.location && <div>{status.location}</div>}
        </div>
      )}

      {/* Ping Results */}
      {ping_results && ping_results.length > 0 && (
        <div className="space-y-2 border-t border-gray-200 dark:border-gray-700 pt-2">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            Connection Tests
          </h4>
          {ping_results.map((result, index) => (
            <PingResultItem key={index} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}
