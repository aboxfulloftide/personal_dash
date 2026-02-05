import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

/**
 * Hook for widget data fetching with auto-refresh.
 *
 * Usage in a widget component:
 *   const { data, loading, error, lastUpdated, refresh } = useWidgetData({
 *     endpoint: '/widgets/weather/data',
 *     params: { location: config.location },
 *     refreshInterval: config.refresh_interval || 300,
 *     enabled: true,
 *   });
 *
 * @param {Object} options
 * @param {string} options.endpoint - API endpoint to fetch from
 * @param {Object} options.params - Query params to pass
 * @param {number} options.refreshInterval - Auto-refresh interval in seconds (0 to disable)
 * @param {boolean} options.enabled - Whether fetching is enabled (default true)
 */
export function useWidgetData({ endpoint, params = {}, refreshInterval = 300, enabled = true }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    if (!endpoint || !enabled) return;

    try {
      setLoading((prev) => prev || data === null); // Only show loading on first fetch
      setError(null);
      const response = await api.get(endpoint, { params });
      setData(response.data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [endpoint, JSON.stringify(params), enabled]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [fetchData, enabled]);

  // Auto-refresh interval
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    if (refreshInterval > 0 && enabled) {
      intervalRef.current = setInterval(fetchData, refreshInterval * 1000);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval, enabled]);

  return { data, loading, error, lastUpdated, refresh: fetchData };
}
