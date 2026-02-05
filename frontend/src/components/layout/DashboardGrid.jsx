import { useState, useCallback } from 'react';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import WidgetContainer from '../widgets/WidgetContainer';

const GRID_COLS = 12;
const ROW_HEIGHT = 100;
const MARGIN = [16, 16];

export default function DashboardGrid({
  widgets,
  layout,
  onLayoutChange,
  onRemoveWidget,
  onWidgetSettings,
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

  return (
    <div ref={handleContainerRef} className="w-full">
      <GridLayout
        className="layout"
        layout={layout}
        cols={GRID_COLS}
        rowHeight={ROW_HEIGHT}
        width={containerWidth}
        margin={MARGIN}
        isDraggable={isEditing}
        isResizable={isEditing}
        onLayoutChange={onLayoutChange}
        draggableHandle=".widget-drag-handle"
        compactType="vertical"
        preventCollision={false}
      >
        {widgets.map((widget) => (
          <div key={widget.id} className={isEditing ? 'widget-drag-handle cursor-move' : ''}>
            <WidgetContainer
              type={widget.type}
              config={widget.config}
              onRemove={() => onRemoveWidget(widget.id)}
              onSettings={() => onWidgetSettings(widget.id)}
              isEditing={isEditing}
            />
          </div>
        ))}
      </GridLayout>
    </div>
  );
}
