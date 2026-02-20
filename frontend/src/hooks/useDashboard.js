import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { getWidget } from '../components/widgets/widgetRegistry';

export function useDashboard() {
  const [widgets, setWidgets] = useState([]);
  const [layout, setLayout] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Load dashboard from API
  const loadDashboard = useCallback(async (options = {}) => {
    const { silent = false } = options;

    try {
      // Only show loading spinner for initial load, not background refreshes
      if (!silent) {
        setLoading(true);
      }
      const response = await api.get('/dashboard/layout');
      setWidgets(response.data.widgets || []);
      setLayout(response.data.layout || []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      if (!silent) {
        setWidgets([]);
        setLayout([]);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  // Save dashboard to API
  const saveDashboard = useCallback(async (newWidgets, newLayout) => {
    try {
      setSaving(true);
      await api.put('/dashboard/layout', {
        widgets: newWidgets,
        layout: newLayout
      });
    } catch (error) {
      console.error('Failed to save dashboard:', error);
    } finally {
      setSaving(false);
    }
  }, []);

  // Add widget
  const addWidget = useCallback((type) => {
    const widgetDef = getWidget(type);
    const id = `widget-${Date.now()}`;

    const newWidget = {
      id,
      type,
      config: { title: widgetDef.name }
    };

    // Find the next open position to the right of existing widgets
    const w = widgetDef.defaultSize.w;
    const h = widgetDef.defaultSize.h;
    let x = 0;
    let y = 0;

    if (layout.length > 0) {
      // Find the bottom-most row
      const maxY = Math.max(...layout.map(l => l.y));
      const bottomRow = layout.filter(l => l.y === maxY);
      // Find the rightmost edge in that row
      const rightEdge = Math.max(...bottomRow.map(l => l.x + l.w));

      if (rightEdge + w <= 12) {
        // Fits to the right on the same row
        x = rightEdge;
        y = maxY;
      } else {
        // Doesn't fit, start a new row
        x = 0;
        y = Infinity;
      }
    }

    const newLayoutItem = {
      i: id,
      x,
      y,
      w,
      h,
      minW: widgetDef.minSize?.w || 1,
      minH: widgetDef.minSize?.h || 1,
      maxW: widgetDef.maxSize?.w || 12,
      maxH: widgetDef.maxSize?.h || 10
    };

    const newWidgets = [...widgets, newWidget];
    const newLayout = [...layout, newLayoutItem];

    setWidgets(newWidgets);
    setLayout(newLayout);
    saveDashboard(newWidgets, newLayout);
  }, [widgets, layout, saveDashboard]);

  // Remove widget
  const removeWidget = useCallback((widgetId) => {
    const newWidgets = widgets.filter(w => w.id !== widgetId);
    const newLayout = layout.filter(l => l.i !== widgetId);

    setWidgets(newWidgets);
    setLayout(newLayout);
    saveDashboard(newWidgets, newLayout);
  }, [widgets, layout, saveDashboard]);

  // Update layout
  const updateLayout = useCallback((newLayout) => {
    setLayout(newLayout);
    saveDashboard(widgets, newLayout);
  }, [widgets, saveDashboard]);

  // Update widget config
  const updateWidgetConfig = useCallback((widgetId, newConfig) => {
    const newWidgets = widgets.map(w =>
      w.id === widgetId ? { ...w, config: { ...w.config, ...newConfig } } : w
    );
    setWidgets(newWidgets);
    saveDashboard(newWidgets, layout);
  }, [widgets, layout, saveDashboard]);

  // Acknowledge alert
  const acknowledgeAlert = useCallback(async (widgetId) => {
    try {
      await api.post(`/widgets/${widgetId}/acknowledge`);
      // Silent reload so the overlay dismisses cleanly without a full-page flash
      await loadDashboard({ silent: true });
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  }, [loadDashboard]);

  useEffect(() => {
    // Initial load with loading spinner
    loadDashboard();

    // Poll for updates every 60 seconds (silent background refresh)
    const pollInterval = setInterval(() => {
      loadDashboard({ silent: true });
    }, 60000); // 60 seconds

    return () => clearInterval(pollInterval);
  }, [loadDashboard]);

  return {
    widgets,
    layout,
    loading,
    saving,
    addWidget,
    removeWidget,
    updateLayout,
    updateWidgetConfig,
    acknowledgeAlert,
    reload: loadDashboard
  };
}
