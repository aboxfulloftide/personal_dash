import { useWidgetData } from '../../hooks/useWidgetData';

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function getBarColor(percent) {
  if (percent >= 90) return 'bg-red-500';
  if (percent >= 70) return 'bg-yellow-500';
  return 'bg-green-500';
}

function MetricBar({ label, percent }) {
  const safePercent = percent ?? 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-14 text-xs text-gray-500 dark:text-gray-400">{label}</span>
      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getBarColor(safePercent)} transition-all duration-300`}
          style={{ width: `${Math.min(safePercent, 100)}%` }}
        />
      </div>
      <span className="w-10 text-xs text-right text-gray-600 dark:text-gray-300">
        {safePercent.toFixed(0)}%
      </span>
    </div>
  );
}

function StatusIndicator({ isOnline, serverName }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
          {serverName}
        </span>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded ${
        isOnline
          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      }`}>
        {isOnline ? 'online' : 'offline'}
      </span>
    </div>
  );
}

function NetworkStats({ networkIn, networkOut }) {
  return (
    <div className="flex items-center justify-center gap-4 py-2 border-t border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
        <span>{formatBytes(networkIn)}</span>
      </div>
      <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
        <span>{formatBytes(networkOut)}</span>
      </div>
    </div>
  );
}

function ContainerList({ containers }) {
  if (!containers || containers.length === 0) {
    return (
      <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-2">
        No containers
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {containers.map((container) => (
        <div
          key={container.container_id || container.name}
          className="flex items-center justify-between text-xs"
        >
          <div className="flex items-center gap-2 min-w-0">
            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
              container.status === 'running' ? 'bg-green-500' : 'bg-gray-400'
            }`} />
            <span className="text-gray-700 dark:text-gray-300 truncate">
              {container.name}
            </span>
          </div>
          <span className="text-gray-500 dark:text-gray-400 flex-shrink-0 ml-2">
            {container.cpu_percent?.toFixed(1) ?? '—'}%
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ServerMonitorWidget({ config }) {
  const { data, loading, error } = useWidgetData({
    endpoint: `/servers/${config.server_id}`,
    refreshInterval: config.refresh_interval || 60,
    enabled: !!config.server_id,
  });

  if (!config.server_id) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
        </svg>
        <p className="text-sm">No server configured</p>
        <p className="text-xs mt-1">Open settings to select a server</p>
      </div>
    );
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
      <div className="flex flex-col items-center justify-center h-full text-red-500">
        <p className="text-sm text-center">{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { server, recent_metrics, containers } = data;
  const latestMetric = recent_metrics?.[0] || {};

  return (
    <div className="h-full flex flex-col">
      <StatusIndicator isOnline={server.is_online} serverName={server.name} />

      <div className="space-y-2 flex-shrink-0">
        <MetricBar label="CPU" percent={latestMetric.cpu_percent} />
        <MetricBar label="Memory" percent={latestMetric.memory_percent} />
        <MetricBar label="Disk" percent={latestMetric.disk_percent} />
      </div>

      <NetworkStats
        networkIn={latestMetric.network_in}
        networkOut={latestMetric.network_out}
      />

      {config.show_docker !== false && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-1 overflow-auto">
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            Docker Containers
          </div>
          <ContainerList containers={containers} />
        </div>
      )}
    </div>
  );
}
