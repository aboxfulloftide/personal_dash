import { useState } from 'react';
import DashboardHeader from '../components/layout/DashboardHeader';
import DashboardGrid from '../components/layout/DashboardGrid';
import AddWidgetModal from '../components/layout/AddWidgetModal';
import WidgetSettingsModal from '../components/widgets/WidgetSettingsModal';
import { useDashboard } from '../hooks/useDashboard';

export default function DashboardPage() {
  const [isEditing, setIsEditing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [settingsWidget, setSettingsWidget] = useState(null);

  const {
    widgets,
    layout,
    loading,
    addWidget,
    removeWidget,
    updateLayout,
    updateWidgetConfig
  } = useDashboard();

  const handleWidgetSettings = (widgetId) => {
    const widget = widgets.find((w) => w.id === widgetId);
    if (widget) {
      setSettingsWidget(widget);
    }
  };

  const handleSaveSettings = (widgetId, newConfig) => {
    updateWidgetConfig(widgetId, newConfig);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <DashboardHeader
        isEditing={isEditing}
        onToggleEdit={() => setIsEditing(!isEditing)}
        onAddWidget={() => setShowAddModal(true)}
      />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {widgets.length === 0 ? (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No widgets yet
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Click "Edit" then "Add Widget" to get started
            </p>
            <button
              onClick={() => {
                setIsEditing(true);
                setShowAddModal(true);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Add Your First Widget
            </button>
          </div>
        ) : (
          <DashboardGrid
            widgets={widgets}
            layout={layout}
            onLayoutChange={updateLayout}
            onRemoveWidget={removeWidget}
            onWidgetSettings={handleWidgetSettings}
            isEditing={isEditing}
          />
        )}
      </main>

      <AddWidgetModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={addWidget}
      />

      <WidgetSettingsModal
        isOpen={!!settingsWidget}
        widgetId={settingsWidget?.id}
        widgetType={settingsWidget?.type}
        currentConfig={settingsWidget?.config || {}}
        onSave={handleSaveSettings}
        onClose={() => setSettingsWidget(null)}
      />
    </div>
  );
}
