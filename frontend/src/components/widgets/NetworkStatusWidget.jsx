import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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

function UptimeCard({ stat }) {
  const getUptimeColor = (uptime) => {
    if (uptime >= 99.5) return 'green';
    if (uptime >= 95) return 'yellow';
    return 'red';
  };

  const colorClass = getUptimeColor(stat.uptime_24h);
  const colorConfig = {
    green: {
      bg: 'bg-green-50 dark:bg-green-900/10',
      text: 'text-green-700 dark:text-green-300',
      dot: 'bg-green-500',
    },
    yellow: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/10',
      text: 'text-yellow-700 dark:text-yellow-300',
      dot: 'bg-yellow-500',
    },
    red: {
      bg: 'bg-red-50 dark:bg-red-900/10',
      text: 'text-red-700 dark:text-red-300',
      dot: 'bg-red-500',
    },
  };

  const colors = colorConfig[colorClass];

  return (
    <div className={`p-2 rounded ${colors.bg}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${colors.dot}`}></span>
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
            {stat.target_name}
          </span>
        </div>
        <span className={`text-xs font-bold ${colors.text}`}>
          {stat.uptime_24h.toFixed(2)}%
        </span>
      </div>
      <div className="grid grid-cols-3 gap-1 text-xs text-gray-500 dark:text-gray-400">
        <div>
          <div className="text-gray-400 dark:text-gray-500">7d</div>
          <div className={colors.text}>{stat.uptime_7d.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-gray-400 dark:text-gray-500">30d</div>
          <div className={colors.text}>{stat.uptime_30d.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-gray-400 dark:text-gray-500">Checks</div>
          <div>{stat.successful_checks_24h}/{stat.total_checks_24h}</div>
        </div>
      </div>
    </div>
  );
}

function MiniSparkline({ dataPoints }) {
  if (!dataPoints || dataPoints.length < 2) {
    return (
      <div className="h-8 flex items-center justify-center text-xs text-gray-400">
        No data
      </div>
    );
  }

  // Format data for Recharts
  const chartData = dataPoints.map((point, index) => ({
    index,
    latency: point.is_reachable ? point.latency_ms : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={30}>
      <LineChart data={chartData} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey="latency"
          stroke="#3b82f6"
          strokeWidth={1.5}
          dot={false}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function DetailedHistoryChart({ historyData, timeRange }) {
  if (!historyData || historyData.targets.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-400">
        No historical data available
      </div>
    );
  }

  // Prepare chart data by combining all targets
  const allDataPoints = new Map();
  const targetColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  historyData.targets.forEach((target) => {
    target.data_points.forEach((point) => {
      const timestamp = new Date(point.timestamp).getTime();
      if (!allDataPoints.has(timestamp)) {
        allDataPoints.set(timestamp, { timestamp });
      }
      const dataPoint = allDataPoints.get(timestamp);
      dataPoint[target.target_name] = point.is_reachable ? point.latency_ms : null;
    });
  });

  const chartData = Array.from(allDataPoints.values()).sort((a, b) => a.timestamp - b.timestamp);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    if (timeRange === '24h') {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (timeRange === '7d') {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          stroke="#9ca3af"
          fontSize={10}
          tickCount={5}
        />
        <YAxis
          label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
          stroke="#9ca3af"
          fontSize={10}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '4px',
            fontSize: '12px',
          }}
          labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
        />
        <Legend wrapperStyle={{ fontSize: '11px' }} />
        {historyData.targets.map((target, index) => (
          <Line
            key={target.target_host}
            type="monotone"
            dataKey={target.target_name}
            stroke={targetColors[index % targetColors.length]}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default function NetworkStatusWidget({ config }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uptimeStats, setUptimeStats] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');
  const intervalRef = useRef(null);

  // Speed test state
  const [speedTestData, setSpeedTestData] = useState(null);
  const [speedTestHistory, setSpeedTestHistory] = useState(null);
  const [runningSpeedTest, setRunningSpeedTest] = useState(false);
  const [speedTestError, setSpeedTestError] = useState(null);
  const [showSpeedTestHistory, setShowSpeedTestHistory] = useState(false);
  const [speedTestTimeRange, setSpeedTestTimeRange] = useState('7d');
  const [rateLimitReset, setRateLimitReset] = useState(null);

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

  const fetchUptimeStats = useCallback(async () => {
    try {
      const response = await api.get('/network/uptime');
      setUptimeStats(response.data);
    } catch (err) {
      console.error('Failed to fetch uptime stats:', err);
    }
  }, []);

  const fetchHistory = useCallback(async (hours = 24) => {
    try {
      const response = await api.get(`/network/ping-history?hours=${hours}`);
      setHistoryData(response.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  }, []);

  const runSpeedTest = useCallback(async () => {
    try {
      setRunningSpeedTest(true);
      setSpeedTestError(null);

      const response = await api.post('/network/speed-test', {});
      setSpeedTestData(response.data.result);
      setRateLimitReset(response.data.rate_limit_reset);

      // Refresh history if it's open
      if (showSpeedTestHistory) {
        const hours = speedTestTimeRange === '24h' ? 24 : speedTestTimeRange === '7d' ? 168 : 720;
        await fetchSpeedTestHistory(hours);
      }
    } catch (err) {
      if (err.response?.status === 429) {
        const detail = err.response.data.detail;
        setSpeedTestError(detail.message || 'Rate limit exceeded');
        setRateLimitReset(detail.rate_limit_reset);
      } else {
        setSpeedTestError(err.response?.data?.detail || err.message || 'Failed to run speed test');
      }
    } finally {
      setRunningSpeedTest(false);
    }
  }, [showSpeedTestHistory, speedTestTimeRange]);

  const fetchSpeedTestStats = useCallback(async () => {
    try {
      const response = await api.get('/network/speed-test-stats');
      if (response.data.latest_test) {
        setSpeedTestData(response.data.latest_test);
      }
    } catch (err) {
      console.error('Failed to fetch speed test stats:', err);
    }
  }, []);

  const fetchSpeedTestHistory = useCallback(async (hours = 168) => {
    try {
      const response = await api.get(`/network/speed-test-history?hours=${hours}`);
      setSpeedTestHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch speed test history:', err);
    }
  }, []);

  // Initial fetch - get current status, uptime stats, and 24h history for sparklines
  useEffect(() => {
    fetchData();
    fetchUptimeStats();
    fetchHistory(24); // Fetch 24h history for sparklines
    fetchSpeedTestStats(); // Fetch latest speed test
  }, [fetchData, fetchUptimeStats, fetchHistory, fetchSpeedTestStats]);

  // Fetch history when time range changes (only when detailed view is expanded)
  useEffect(() => {
    if (showHistory) {
      const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720;
      fetchHistory(hours);
    }
  }, [showHistory, timeRange, fetchHistory]);

  // Fetch speed test history when expanded or time range changes
  useEffect(() => {
    if (showSpeedTestHistory) {
      const hours = speedTestTimeRange === '24h' ? 24 : speedTestTimeRange === '7d' ? 168 : 720;
      fetchSpeedTestHistory(hours);
    }
  }, [showSpeedTestHistory, speedTestTimeRange, fetchSpeedTestHistory]);

  // Auto-refresh interval
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    const refreshInterval = config.refresh_interval || 60;
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchData();
        fetchUptimeStats();
        // Refresh history based on current view
        if (showHistory) {
          const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720;
          fetchHistory(hours);
        } else {
          // Always refresh 24h sparklines
          fetchHistory(24);
        }
      }, refreshInterval * 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, fetchUptimeStats, fetchHistory, showHistory, timeRange, config.refresh_interval]);

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

      {/* Uptime Stats Section */}
      {uptimeStats && uptimeStats.targets && uptimeStats.targets.length > 0 && (
        <div className="space-y-2 border-t border-gray-200 dark:border-gray-700 pt-2">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            Uptime Statistics
          </h4>
          {uptimeStats.targets.map((stat, index) => (
            <UptimeCard key={index} stat={stat} />
          ))}
        </div>
      )}

      {/* Speed Test Section */}
      <div className="space-y-2 border-t border-gray-200 dark:border-gray-700 pt-2">
        <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
          Network Speed
        </h4>

        {/* Speed Test Button */}
        <button
          onClick={runSpeedTest}
          disabled={runningSpeedTest || rateLimitReset !== null}
          className={`w-full py-2 px-3 text-sm font-medium rounded transition-colors ${
            runningSpeedTest || rateLimitReset !== null
              ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {runningSpeedTest ? (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Testing... (30-60s)</span>
            </div>
          ) : rateLimitReset ? (
            'Rate Limited - Wait Before Testing'
          ) : (
            'Run Speed Test'
          )}
        </button>

        {/* Speed Test Error */}
        {speedTestError && (
          <div className="p-2 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-300">
            {speedTestError}
          </div>
        )}

        {/* Latest Speed Test Result */}
        {speedTestData && speedTestData.is_successful && (
          <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded space-y-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Download</div>
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {speedTestData.download_mbps?.toFixed(1)} Mbps
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Upload</div>
                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {speedTestData.upload_mbps?.toFixed(1)} Mbps
                </div>
              </div>
            </div>
            {speedTestData.ping_ms !== null && (
              <div className="text-xs text-gray-600 dark:text-gray-400">
                Ping: {speedTestData.ping_ms?.toFixed(0)} ms
              </div>
            )}
            {speedTestData.server_location && (
              <div className="text-xs text-gray-500 dark:text-gray-500">
                Server: {speedTestData.server_location}
              </div>
            )}
            <div className="text-xs text-gray-400 dark:text-gray-500">
              {new Date(speedTestData.timestamp).toLocaleString()}
            </div>
          </div>
        )}

        {/* Speed Test History Toggle */}
        {speedTestData && (
          <div className="pt-2">
            {!showSpeedTestHistory ? (
              <button
                onClick={() => setShowSpeedTestHistory(true)}
                className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
              >
                <span>Show Speed History</span>
                <span>▼</span>
              </button>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Speed History
                  </h5>
                  <button
                    onClick={() => setShowSpeedTestHistory(false)}
                    className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    Hide ▲
                  </button>
                </div>

                {/* Time Range Selector */}
                <div className="flex gap-2">
                  {['24h', '7d', '30d'].map((range) => (
                    <button
                      key={range}
                      onClick={() => setSpeedTestTimeRange(range)}
                      className={`flex-1 py-1 px-2 text-xs font-medium rounded transition-colors ${
                        speedTestTimeRange === range
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>

                {/* Speed Test History Chart */}
                {speedTestHistory && speedTestHistory.tests && speedTestHistory.tests.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart
                      data={speedTestHistory.tests.map((test) => ({
                        timestamp: new Date(test.timestamp).getTime(),
                        download: test.is_successful ? test.download_mbps : null,
                        upload: test.is_successful ? test.upload_mbps : null,
                      }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                      <XAxis
                        dataKey="timestamp"
                        tickFormatter={(timestamp) => {
                          const date = new Date(timestamp);
                          if (speedTestTimeRange === '24h') {
                            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                          } else if (speedTestTimeRange === '7d') {
                            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
                          } else {
                            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
                          }
                        }}
                        stroke="#9ca3af"
                        fontSize={10}
                        tickCount={5}
                      />
                      <YAxis
                        label={{ value: 'Speed (Mbps)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
                        stroke="#9ca3af"
                        fontSize={10}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '4px',
                          fontSize: '12px',
                        }}
                        labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Line
                        type="monotone"
                        dataKey="download"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                        connectNulls={false}
                        name="Download"
                      />
                      <Line
                        type="monotone"
                        dataKey="upload"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                        connectNulls={false}
                        name="Upload"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-400 text-xs">
                    No speed test history available
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quick Sparklines Section */}
      {historyData && historyData.targets && historyData.targets.length > 0 && (
        <div className="space-y-2 border-t border-gray-200 dark:border-gray-700 pt-2">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            24h Latency Trends
          </h4>
          {historyData.targets.map((target, index) => (
            <div key={index} className="space-y-1">
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {target.target_name}
              </div>
              <MiniSparkline dataPoints={target.data_points} />
            </div>
          ))}
        </div>
      )}

      {/* Expandable History Section */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
        {!showHistory ? (
          <button
            onClick={() => setShowHistory(true)}
            className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
          >
            <span>Show Detailed History</span>
            <span>▼</span>
          </button>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Historical Performance
              </h4>
              <button
                onClick={() => setShowHistory(false)}
                className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                Hide ▲
              </button>
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`flex-1 py-1 px-2 text-xs font-medium rounded transition-colors ${
                    timeRange === range
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>

            {/* Detailed Chart */}
            <DetailedHistoryChart historyData={historyData} timeRange={timeRange} />
          </div>
        )}
      </div>
    </div>
  );
}
