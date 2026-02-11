import { useState, useEffect } from 'react';
import { useWidgetData } from '../../hooks/useWidgetData';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function formatDriveCapacity(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 GB';
  const gb = bytes / (1024 ** 3);
  if (gb < 1024) {
    return `${gb.toFixed(1)} GB`;
  }
  const tb = gb / 1024;
  return `${tb.toFixed(2)} TB`;
}

function getDriveIcon(fstype, mountPoint) {
  if (!mountPoint) return '💾';
  if (mountPoint === '/') return '💾';
  if (mountPoint.includes('boot')) return '⚙️';
  if (mountPoint.includes('home')) return '🏠';
  if (mountPoint.includes('mnt') || mountPoint.includes('media')) return '📁';
  if (fstype && (fstype.includes('nfs') || fstype.includes('cifs') || fstype.includes('smb'))) return '🌐';
  return '💾';
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

function ProcessList({ processes, serverId, onRefresh, isEditing }) {
  const [hoveredId, setHoveredId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [processToDelete, setProcessToDelete] = useState(null);

  const handleDeleteConfirm = async () => {
    if (!processToDelete) return;

    setDeletingId(processToDelete.id);
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/servers/${serverId}/processes/${processToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      onRefresh();
    } catch (err) {
      console.error('Failed to delete process:', err);
      alert('Failed to remove process');
    } finally {
      setDeletingId(null);
      setProcessToDelete(null);
    }
  };

  if (!processes || processes.length === 0) {
    return (
      <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-2">
        No processes monitored
      </div>
    );
  }

  return (
    <>
      <div className="space-y-1">
        {processes.map((process) => (
          <div
            key={process.id}
            className="flex items-center justify-between text-xs group"
            onMouseEnter={() => setHoveredId(process.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                process.is_running ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-gray-700 dark:text-gray-300 truncate">
                {process.process_name}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {process.is_running && (
                <span className="text-gray-500 dark:text-gray-400">
                  {process.cpu_percent?.toFixed(1) ?? '—'}%
                </span>
              )}
              {isEditing && hoveredId === process.id && (
                <button
                  onClick={() => setProcessToDelete(process)}
                  disabled={deletingId === process.id}
                  className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 ml-1"
                  title="Remove process"
                >
                  {deletingId === process.id ? '...' : '✕'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      {processToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setProcessToDelete(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Remove Process?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Remove <span className="font-semibold">{processToDelete.process_name}</span> from monitoring?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setProcessToDelete(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AddProcessModal({ isOpen, onClose, serverId, onSuccess }) {
  const [processName, setProcessName] = useState('');
  const [matchPattern, setMatchPattern] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!processName.trim() || !matchPattern.trim()) {
      alert('Please fill in all fields');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/servers/${serverId}/processes`,
        {
          process_name: processName.trim(),
          match_pattern: matchPattern.trim(),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setProcessName('');
      setMatchPattern('');
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to add process:', err);
      alert('Failed to add process');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Add Process to Monitor
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Process Name
              </label>
              <input
                type="text"
                value={processName}
                onChange={(e) => setProcessName(e.target.value)}
                placeholder="e.g., MySQL Database"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={submitting}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Display name for the process
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Match Pattern
              </label>
              <input
                type="text"
                value={matchPattern}
                onChange={(e) => setMatchPattern(e.target.value)}
                placeholder="e.g., mysqld"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={submitting}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Search for this in process name or command line
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Adding...' : 'Add Process'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DriveList({ drives, serverId, onRefresh, isEditing }) {
  const [hoveredId, setHoveredId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [driveToDelete, setDriveToDelete] = useState(null);

  const handleDeleteConfirm = async () => {
    if (!driveToDelete) return;

    setDeletingId(driveToDelete.id);
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/servers/${serverId}/drives/${driveToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      onRefresh();
    } catch (err) {
      console.error('Failed to delete drive:', err);
      alert('Failed to remove drive');
    } finally {
      setDeletingId(null);
      setDriveToDelete(null);
    }
  };

  if (!drives || drives.length === 0) {
    return (
      <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-2">
        No drives monitored
      </div>
    );
  }

  return (
    <>
      <div className="space-y-1.5">
        {drives.map((drive) => (
          <div
            key={drive.id}
            className="text-xs group"
            onMouseEnter={() => setHoveredId(drive.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 min-w-0 flex-1">
                <span className="flex-shrink-0">{getDriveIcon(drive.fstype, drive.mount_point)}</span>
                <span className="text-gray-700 dark:text-gray-300 font-medium truncate">
                  {drive.mount_point}
                </span>
                {!drive.is_mounted && (
                  <span className="text-orange-500" title="Unmounted">⚠️</span>
                )}
                {drive.is_readonly && (
                  <span className="text-blue-500" title="Read-only">🔒</span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {drive.is_mounted && drive.total_bytes && (
                  <span className="text-gray-500 dark:text-gray-400">
                    {formatDriveCapacity(drive.used_bytes)} / {formatDriveCapacity(drive.total_bytes)}
                  </span>
                )}
                {isEditing && hoveredId === drive.id && (
                  <button
                    onClick={() => setDriveToDelete(drive)}
                    disabled={deletingId === drive.id}
                    className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 ml-1"
                    title="Remove drive"
                  >
                    {deletingId === drive.id ? '...' : '✕'}
                  </button>
                )}
              </div>
            </div>
            {drive.is_mounted && drive.percent_used !== null && (
              <div className="flex items-center gap-2 ml-5">
                <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(drive.percent_used)} transition-all duration-300`}
                    style={{ width: `${Math.min(drive.percent_used, 100)}%` }}
                  />
                </div>
                <span className="w-10 text-xs text-right text-gray-600 dark:text-gray-300">
                  {drive.percent_used.toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Delete Confirmation Modal */}
      {driveToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDriveToDelete(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Remove Drive?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Remove <span className="font-semibold">{driveToDelete.mount_point}</span> from monitoring?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDriveToDelete(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AddDriveModal({ isOpen, onClose, serverId, onSuccess }) {
  const [mountPoint, setMountPoint] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const trimmedMount = mountPoint.trim();
    if (!trimmedMount) {
      alert('Please enter a mount point');
      return;
    }

    if (!trimmedMount.startsWith('/')) {
      alert('Mount point must start with /');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/servers/${serverId}/drives`,
        {
          mount_point: trimmedMount,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setMountPoint('');
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Failed to add drive:', err);
      alert(err.response?.data?.detail || 'Failed to add drive');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Add Drive to Monitor
        </h3>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Mount Point
              </label>
              <input
                type="text"
                value={mountPoint}
                onChange={(e) => setMountPoint(e.target.value)}
                placeholder="/mnt/data"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={submitting}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Path to the mount point (e.g., /, /home, /mnt/nas)
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Adding...' : 'Add Drive'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Single server view (detailed)
function SingleServerView({ serverId, config, isEditing }) {
  const [showAddProcessModal, setShowAddProcessModal] = useState(false);
  const [showAddDriveModal, setShowAddDriveModal] = useState(false);

  const { data, loading, error, refresh } = useWidgetData({
    endpoint: `/servers/${serverId}`,
    refreshInterval: config.refresh_interval || 60,
    enabled: !!serverId,
  });

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

  const { server, recent_metrics, containers, processes, drives } = data;
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

      {config.show_processes !== false && processes && processes.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Processes
            </div>
            {isEditing && (
              <button
                onClick={() => setShowAddProcessModal(true)}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                title="Add process to monitor"
              >
                + Add
              </button>
            )}
          </div>
          <ProcessList
            processes={processes}
            serverId={serverId}
            onRefresh={refresh}
            isEditing={isEditing}
          />
        </div>
      )}

      {/* Show add process button in edit mode even if no processes */}
      {config.show_processes !== false && isEditing && (!processes || processes.length === 0) && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Processes
            </div>
            <button
              onClick={() => setShowAddProcessModal(true)}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              title="Add process to monitor"
            >
              + Add
            </button>
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-1">
            No processes
          </div>
        </div>
      )}

      {config.show_drives !== false && drives && drives.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Drives
            </div>
            {isEditing && (
              <button
                onClick={() => setShowAddDriveModal(true)}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                title="Add drive to monitor"
              >
                + Add
              </button>
            )}
          </div>
          <DriveList
            drives={drives}
            serverId={serverId}
            onRefresh={refresh}
            isEditing={isEditing}
          />
        </div>
      )}

      {/* Show add drive button in edit mode even if no drives */}
      {config.show_drives !== false && isEditing && (!drives || drives.length === 0) && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Drives
            </div>
            <button
              onClick={() => setShowAddDriveModal(true)}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              title="Add drive to monitor"
            >
              + Add
            </button>
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-1">
            No drives
          </div>
        </div>
      )}

      {config.show_docker !== false && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex-1 overflow-auto">
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            Docker Containers
          </div>
          <ContainerList containers={containers} />
        </div>
      )}

      <AddProcessModal
        isOpen={showAddProcessModal}
        onClose={() => setShowAddProcessModal(false)}
        serverId={serverId}
        onSuccess={refresh}
      />

      <AddDriveModal
        isOpen={showAddDriveModal}
        onClose={() => setShowAddDriveModal(false)}
        serverId={serverId}
        onSuccess={refresh}
      />
    </div>
  );
}

// Multi-server view (compact cards)
function MultiServerView({ serverIds, config, isEditing }) {
  const [serversData, setServersData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddProcessModal, setShowAddProcessModal] = useState(false);
  const [showAddDriveModal, setShowAddDriveModal] = useState(false);
  const [selectedServerId, setSelectedServerId] = useState(null);
  const [processToDelete, setProcessToDelete] = useState(null);
  const [deletingProcessId, setDeletingProcessId] = useState(null);
  const [hoveredProcessId, setHoveredProcessId] = useState(null);
  const [driveToDelete, setDriveToDelete] = useState(null);
  const [deletingDriveId, setDeletingDriveId] = useState(null);
  const [hoveredDriveId, setHoveredDriveId] = useState(null);

  const fetchServers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const promises = serverIds.map(id =>
        axios.get(`${API_BASE_URL}/servers/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(err => ({ error: true, id, message: err.response?.data?.detail || 'Failed to load' }))
      );
      const results = await Promise.all(promises);
      setServersData(results.map(r => r.error ? r : r.data));
      setError(null);
    } catch (err) {
      setError('Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
    const interval = setInterval(fetchServers, (config.refresh_interval || 60) * 1000);
    return () => clearInterval(interval);
  }, [serverIds.join(','), config.refresh_interval]);

  const handleDeleteProcess = async () => {
    if (!processToDelete) return;

    setDeletingProcessId(processToDelete.id);
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/servers/${processToDelete.serverId}/processes/${processToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchServers(); // Refresh data
    } catch (err) {
      console.error('Failed to delete process:', err);
      alert('Failed to remove process');
    } finally {
      setDeletingProcessId(null);
      setProcessToDelete(null);
    }
  };

  const handleDeleteDrive = async () => {
    if (!driveToDelete) return;

    setDeletingDriveId(driveToDelete.id);
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/servers/${driveToDelete.serverId}/drives/${driveToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchServers(); // Refresh data
    } catch (err) {
      console.error('Failed to delete drive:', err);
      alert('Failed to remove drive');
    } finally {
      setDeletingDriveId(null);
      setDriveToDelete(null);
    }
  };

  if (loading && serversData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto space-y-2 p-1">
      {serversData.map((serverData) => {
        if (serverData.error) {
          return (
            <div key={serverData.id} className="p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-700 dark:text-red-400">Server {serverData.id}: {serverData.message}</p>
            </div>
          );
        }

        const { server, recent_metrics } = serverData;
        const latestMetric = recent_metrics?.[0] || {};

        return (
          <div key={server.id} className="p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${server.is_online ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium text-gray-900 dark:text-white">{server.name}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${
                server.is_online
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              }`}>
                {server.is_online ? 'online' : 'offline'}
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-12 text-xs text-gray-500 dark:text-gray-400">CPU</span>
                <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(latestMetric.cpu_percent || 0)}`}
                    style={{ width: `${Math.min(latestMetric.cpu_percent || 0, 100)}%` }}
                  />
                </div>
                <span className="w-10 text-xs text-right text-gray-600 dark:text-gray-300">
                  {(latestMetric.cpu_percent || 0).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-12 text-xs text-gray-500 dark:text-gray-400">Memory</span>
                <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(latestMetric.memory_percent || 0)}`}
                    style={{ width: `${Math.min(latestMetric.memory_percent || 0, 100)}%` }}
                  />
                </div>
                <span className="w-10 text-xs text-right text-gray-600 dark:text-gray-300">
                  {(latestMetric.memory_percent || 0).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-12 text-xs text-gray-500 dark:text-gray-400">Disk</span>
                <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(latestMetric.disk_percent || 0)}`}
                    style={{ width: `${Math.min(latestMetric.disk_percent || 0, 100)}%` }}
                  />
                </div>
                <span className="w-10 text-xs text-right text-gray-600 dark:text-gray-300">
                  {(latestMetric.disk_percent || 0).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Processes - only show if has processes OR in edit mode */}
            {config.show_processes !== false && (serverData.processes?.length > 0 || isEditing) && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400">Processes</div>
                  {isEditing && (
                    <button
                      onClick={() => {
                        setSelectedServerId(server.id);
                        setShowAddProcessModal(true);
                      }}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      + Add
                    </button>
                  )}
                </div>
                {serverData.processes && serverData.processes.length > 0 ? (
                  <div className="space-y-1">
                    {serverData.processes.map((process) => (
                      <div
                        key={process.id}
                        className="flex items-center justify-between text-xs group"
                        onMouseEnter={() => setHoveredProcessId(process.id)}
                        onMouseLeave={() => setHoveredProcessId(null)}
                      >
                        <div className="flex items-center gap-1.5 min-w-0 flex-1">
                          <div className={`w-1 h-1 rounded-full flex-shrink-0 ${
                            process.is_running ? 'bg-green-500' : 'bg-red-500'
                          }`} />
                          <span className="text-gray-700 dark:text-gray-300 truncate">{process.process_name}</span>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {process.is_running && (
                            <span className="text-gray-500 dark:text-gray-400">
                              {process.cpu_percent?.toFixed(1) ?? '—'}%
                            </span>
                          )}
                          {isEditing && hoveredProcessId === process.id && (
                            <button
                              onClick={() => setProcessToDelete({ ...process, serverId: server.id })}
                              disabled={deletingProcessId === process.id}
                              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 ml-1"
                            >
                              {deletingProcessId === process.id ? '...' : '✕'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-1">
                    No processes
                  </div>
                )}
              </div>
            )}

            {/* Drives */}
            {config.show_drives !== false && (serverData.drives?.length > 0 || isEditing) && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400">Drives</div>
                  {isEditing && (
                    <button
                      onClick={() => {
                        setSelectedServerId(server.id);
                        setShowAddDriveModal(true);
                      }}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      + Add
                    </button>
                  )}
                </div>
                {serverData.drives && serverData.drives.length > 0 ? (
                  <div className="space-y-1">
                    {serverData.drives.map((drive) => (
                      <div
                        key={drive.id}
                        className="text-xs"
                        onMouseEnter={() => setHoveredDriveId(drive.id)}
                        onMouseLeave={() => setHoveredDriveId(null)}
                      >
                        <div className="flex items-center justify-between mb-0.5">
                          <div className="flex items-center gap-1 min-w-0 flex-1">
                            <span className="flex-shrink-0 text-[10px]">{getDriveIcon(drive.fstype, drive.mount_point)}</span>
                            <span className="text-gray-700 dark:text-gray-300 truncate">{drive.mount_point}</span>
                            {!drive.is_mounted && <span className="text-orange-500 text-[10px]" title="Unmounted">⚠️</span>}
                            {drive.is_readonly && <span className="text-blue-500 text-[10px]" title="Read-only">🔒</span>}
                          </div>
                          {isEditing && hoveredDriveId === drive.id && (
                            <button
                              onClick={() => setDriveToDelete({ ...drive, serverId: server.id })}
                              disabled={deletingDriveId === drive.id}
                              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 ml-1"
                            >
                              {deletingDriveId === drive.id ? '...' : '✕'}
                            </button>
                          )}
                        </div>
                        {drive.is_mounted && drive.percent_used !== null && (
                          <div className="flex items-center gap-1 ml-3.5">
                            <div className="flex-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${getBarColor(drive.percent_used)}`}
                                style={{ width: `${Math.min(drive.percent_used, 100)}%` }}
                              />
                            </div>
                            <span className="w-8 text-[10px] text-right text-gray-600 dark:text-gray-300">
                              {drive.percent_used.toFixed(0)}%
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-400 dark:text-gray-500 text-center py-1">
                    No drives
                  </div>
                )}
              </div>
            )}

            {/* Docker Containers */}
            {config.show_docker !== false && serverData.containers && serverData.containers.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Docker</div>
                <div className="space-y-1">
                  {serverData.containers.map((container) => (
                    <div key={container.id} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 min-w-0 flex-1">
                        <div className={`w-1 h-1 rounded-full flex-shrink-0 ${
                          container.status === 'running' ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                        <span className="text-gray-700 dark:text-gray-300 truncate">{container.name}</span>
                      </div>
                      <span className="text-gray-500 dark:text-gray-400 flex-shrink-0 ml-2">
                        {container.cpu_percent?.toFixed(1) ?? '—'}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Add Process Modal */}
      <AddProcessModal
        isOpen={showAddProcessModal}
        onClose={() => {
          setShowAddProcessModal(false);
          setSelectedServerId(null);
        }}
        serverId={selectedServerId}
        onSuccess={() => {
          fetchServers();
          setShowAddProcessModal(false);
          setSelectedServerId(null);
        }}
      />

      {/* Add Drive Modal */}
      <AddDriveModal
        isOpen={showAddDriveModal}
        onClose={() => {
          setShowAddDriveModal(false);
          setSelectedServerId(null);
        }}
        serverId={selectedServerId}
        onSuccess={() => {
          fetchServers();
          setShowAddDriveModal(false);
          setSelectedServerId(null);
        }}
      />

      {/* Delete Process Confirmation Modal */}
      {processToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setProcessToDelete(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Remove Process?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Remove <span className="font-semibold">{processToDelete.process_name}</span> from monitoring?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setProcessToDelete(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteProcess}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Drive Confirmation Modal */}
      {driveToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDriveToDelete(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Remove Drive?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Remove <span className="font-semibold">{driveToDelete.mount_point}</span> from monitoring?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDriveToDelete(null)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteDrive}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Main export - decides between single and multi-server view
export default function ServerMonitorWidget({ config, isEditing }) {
  // Handle both old (server_id) and new (server_ids) config formats
  const serverIds = config.server_ids || (config.server_id ? [config.server_id] : null);

  if (!serverIds || serverIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
        </svg>
        <p className="text-sm">No servers configured</p>
        <p className="text-xs mt-1">Open settings to select servers</p>
      </div>
    );
  }

  // Single server - use detailed view
  if (serverIds.length === 1) {
    return <SingleServerView serverId={serverIds[0]} config={config} isEditing={isEditing} />;
  }

  // Multiple servers - use compact view
  return <MultiServerView serverIds={serverIds} config={config} isEditing={isEditing} />;
}
