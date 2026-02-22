import { useState, useCallback, useMemo } from 'react';
import { ResponsiveGridLayout, useContainerWidth } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import WidgetContainer from '../widgets/WidgetContainer';

// Desktop: 24 cols (existing layout format)
// Tablet:  12 cols (derived — halved x/w from desktop)
// Mobile:   4 cols (derived — full-width stack in reading order)
const BREAKPOINTS = { lg: 1200, md: 768, sm: 0 };
const COLS = { lg: 24, md: 12, sm: 4 };
const ROW_HEIGHT = 100;
const MARGIN = [16, 16];

/**
 * Auto-derive tablet (md) and mobile (sm) layouts from the saved desktop (lg) layout.
 * The backend only stores the lg layout; the others are computed client-side and never saved.
 */
function deriveLayouts(lgLayout) {
  // Tablet: halve column positions and widths from the 24-col desktop grid
  const mdLayout = lgLayout.map(item => ({
    ...item,
    x: Math.min(Math.floor(item.x / 2), 11),
    w: Math.max(Math.floor(item.w / 2), item.minW || 2),
    maxW: item.maxW ? Math.max(Math.floor(item.maxW / 2), item.minW || 2) : 12,
  }));

  // Mobile: full-width stack, sorted by desktop row then column (natural reading order)
  const sorted = [...lgLayout].sort((a, b) => a.y !== b.y ? a.y - b.y : a.x - b.x);
  let smY = 0;
  const smLayout = sorted.map(item => {
    const smItem = { ...item, x: 0, y: smY, w: 4, minW: 2, maxW: 4 };
    smY += item.h;
    return smItem;
  });

  return { lg: lgLayout, md: mdLayout, sm: smLayout };
}

export default function DashboardGrid({
  widgets,
  layout,
  onLayoutChange,
  onRemoveWidget,
  onWidgetSettings,
  onWidgetConfigChange,
  isEditing
}) {
  const [currentBreakpoint, setCurrentBreakpoint] = useState('lg');
  const { containerRef, width } = useContainerWidth({ initialWidth: 1280 });

  // Layout editing only makes sense on desktop — mobile/tablet are view-only
  const isEditingDesktop = isEditing && currentBreakpoint === 'lg';

  // Derive all breakpoint layouts and apply static flag
  const layouts = useMemo(() => {
    const derived = deriveLayouts(layout);
    const applyStatic = (items, bp) =>
      items.map(item => ({ ...item, static: !isEditing || bp !== 'lg' }));
    return {
      lg: applyStatic(derived.lg, 'lg'),
      md: applyStatic(derived.md, 'md'),
      sm: applyStatic(derived.sm, 'sm'),
    };
  }, [layout, isEditing]);

  const handleLayoutChange = useCallback((currentLayout) => {
    // Only persist when the user is editing on desktop — md/sm layouts are never saved
    if (isEditing && currentBreakpoint === 'lg') {
      onLayoutChange(currentLayout);
    }
  }, [isEditing, currentBreakpoint, onLayoutChange]);

  return (
    <div ref={containerRef} className="w-full">
      {/* Editing is desktop-only — show a hint on smaller screens */}
      {isEditing && currentBreakpoint !== 'lg' && (
        <div className="mb-4 px-3 py-2 bg-yellow-900/30 border border-yellow-700/50 rounded text-xs text-yellow-300 text-center">
          Switch to a wider screen to drag and resize widgets
        </div>
      )}

      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={BREAKPOINTS}
        cols={COLS}
        rowHeight={ROW_HEIGHT}
        margin={MARGIN}
        width={width}
        isDraggable={isEditingDesktop}
        isResizable={isEditingDesktop}
        onLayoutChange={handleLayoutChange}
        onBreakpointChange={(bp) => setCurrentBreakpoint(bp)}
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
              onRemove={() => onRemoveWidget(widget.id)}
              onSettings={() => onWidgetSettings(widget.id)}
              onConfigChange={(newConfig) => onWidgetConfigChange?.(widget.id, newConfig)}
              isEditing={isEditingDesktop}
            />
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  );
}
