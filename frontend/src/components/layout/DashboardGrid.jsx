import { useState, useCallback, useMemo } from 'react';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import WidgetContainer from '../widgets/WidgetContainer';

const GRID_COLS = 24;
const ROW_HEIGHT = 100;
const MARGIN = [16, 16];

export default function DashboardGrid({
  widgets,
  layout,
  onLayoutChange,
  onRemoveWidget,
  onWidgetSettings,
  onWidgetConfigChange,
  onAcknowledgeAlert,
  isEditing
}) {
  const [containerWidth, setContainerWidth] = useState(1200);

  const handleContainerRef = useCallback((node) => {
    if (node) {
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          setContainerWidth(entry.contentRect.width);
        }
      });
      resizeObserver.observe(node);
      return () => resizeObserver.disconnect();
    }
  }, []);

  // Compute layout with alerted widgets moved to top (only when not editing)
  const adjustedLayout = useMemo(() => {

    // In edit mode, use original layout so users can rearrange freely
    if (isEditing) {
      return layout;
    }

    // Identify alerted widgets by severity
    const alertedWidgets = widgets
      .filter(w => w.alert_active)
      .map(w => {
        const layoutItem = layout.find(l => l.i === w.id);
        return {
          ...w,
          layoutItem,
          severityPriority: w.alert_severity === 'critical' ? 0 : w.alert_severity === 'warning' ? 1 : 2
        };
      })
      .sort((a, b) => a.severityPriority - b.severityPriority); // Critical first

    const alertedIds = new Set(alertedWidgets.map(w => w.id));

    // Non-alerted widgets keep their original positions
    const nonAlertedLayout = layout.filter(l => !alertedIds.has(l.i));

    if (alertedWidgets.length === 0) {
      return layout; // No alerts, return original layout
    }

    // Position alerted widgets at the top
    const alertedLayout = [];
    let currentX = 0;
    let currentY = 0;
    let maxHeightInRow = 0;

    for (const widget of alertedWidgets) {
      const { layoutItem } = widget;
      if (!layoutItem) continue;

      const { w, h } = layoutItem;

      // Check if widget fits in current row
      if (currentX + w > GRID_COLS && currentX > 0) {
        // Move to next row
        currentX = 0;
        currentY += maxHeightInRow;
        maxHeightInRow = 0;
      }

      alertedLayout.push({
        ...layoutItem,
        x: currentX,
        y: currentY,
        static: true // Alerted widgets can't be moved
      });

      currentX += w;
      maxHeightInRow = Math.max(maxHeightInRow, h);
    }

    // Calculate how much to shift non-alerted widgets down
    const alertedBottomY = currentY + maxHeightInRow;

    // Shift non-alerted widgets down
    const shiftedLayout = nonAlertedLayout.map(item => ({
      ...item,
      y: item.y + alertedBottomY
    }));

    return [...alertedLayout, ...shiftedLayout];
  }, [widgets, layout, isEditing]);

  // Make all widgets static (non-movable) when not in edit mode
  const layoutWithStatic = adjustedLayout.map(item => ({
    ...item,
    static: !isEditing
  }));

  // Only save layout changes when in edit mode to prevent infinite loops
  // when programmatically adjusting layout for alerts
  const handleLayoutChange = useCallback((newLayout) => {
    if (isEditing) {
      // Only save when user is actively editing
      onLayoutChange(newLayout);
    }
    // Ignore layout changes when not editing (they're just alert adjustments)
  }, [isEditing, onLayoutChange]);

  return (
    <div ref={handleContainerRef} className="w-full">
      <GridLayout
        className="layout"
        layout={layoutWithStatic}
        cols={GRID_COLS}
        rowHeight={ROW_HEIGHT}
        width={containerWidth}
        margin={MARGIN}
        isDraggable={isEditing}
        isResizable={isEditing}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".widget-drag-handle"
        compactType="vertical"
        preventCollision={false}
      >
        {widgets.map((widget) => (
          <div key={widget.id}>
            <WidgetContainer
              type={widget.type}
              config={widget.config}
              widgetId={widget.id}
              alertActive={widget.alert_active || false}
              alertSeverity={widget.alert_severity}
              alertMessage={widget.alert_message}
              onRemove={() => onRemoveWidget(widget.id)}
              onSettings={() => onWidgetSettings(widget.id)}
              onConfigChange={(newConfig) => onWidgetConfigChange?.(widget.id, newConfig)}
              onAcknowledge={onAcknowledgeAlert}
              isEditing={isEditing}
            />
          </div>
        ))}
      </GridLayout>
    </div>
  );
}
