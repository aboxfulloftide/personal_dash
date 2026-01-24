# Task 005: Dashboard Layout & Widget Framework

## Objective
Build the main dashboard layout with drag-and-drop grid system, widget container framework, and dark mode toggle.

## Prerequisites
- Task 004 completed
- Frontend auth working

## Dependencies to Install
```bash
cd frontend
npm install react-grid-layout
```

## Deliverables

### 1. Theme Context

#### src/contexts/ThemeContext.jsx:
```jsx
import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return JSON.parse(saved);
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(prev => !prev);

  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
```

### 2. Widget Registry

#### src/components/widgets/widgetRegistry.js:
```javascript
// Widget registry - add new widgets here
const widgetRegistry = {
  // Example placeholder widgets (to be replaced with real implementations)
  placeholder: {
    component: () => import('./PlaceholderWidget'),
    name: 'Placeholder',
    description: 'Placeholder widget',
    defaultSize: { w: 2, h: 2 },
    minSize: { w: 1, h: 1 },
    maxSize: { w: 4, h: 4 }
  }
};

export function getWidget(type) {
  return widgetRegistry[type] || widgetRegistry.placeholder;
}

export function getAvailableWidgets() {
  return Object.entries(widgetRegistry).map(([type, config]) => ({
    type,
    name: config.name,
    description: config.description,
    defaultSize: config.defaultSize
  }));
}

export default widgetRegistry;
```

### 3. Widget Container Component

#### src/components/widgets/WidgetContainer.jsx:
```jsx
import { Suspense, lazy, useState } from 'react';
import { getWidget } from './widgetRegistry';

function WidgetLoader() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}

function WidgetError({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-red-500 p-4">
      <span className="text-2xl mb-2">⚠️</span>
      <p className="text-sm text-center mb-2">Failed to load widget</p>
      <button
        onClick={onRetry}
        className="text-xs text-blue-500 hover:underline"
      >
        Retry
      </button>
    </div>
  );
}

export default function WidgetContainer({ 
  type, 
  config = {}, 
  onRemove, 
  onSettings,
  isEditing = false 
}) {
  const [error, setError] = useState(null);
  const [retryKey, setRetryKey] = useState(0);

  const widgetDef = getWidget(type);
  const WidgetComponent = lazy(widgetDef.component);

  const handleRetry = () => {
    setError(null);
    setRetryKey(prev => prev + 1);
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      {/* Widget Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
          {config.title || widgetDef.name}
        </h3>
        {isEditing && (
          <div className="flex items-center gap-1">
            <button
              onClick={onSettings}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              title="Settings"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <button
              onClick={onRemove}
              className="p-1 text-gray-400 hover:text-red-500"
              title="Remove"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Widget Content */}
      <div className="flex-1 overflow-auto p-3">
        {error ? (
          <WidgetError error={error} onRetry={handleRetry} />
        ) : (
          <Suspense fallback={<WidgetLoader />} key={retryKey}>
            <WidgetComponent config={config} />
          </Suspense>
        )}
      </div>
    </div>
  );
}
```

### 4. Placeholder Widget

#### src/components/widgets/PlaceholderWidget.jsx:
```jsx
export default function PlaceholderWidget({ config }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-400">
      <span className="text-4xl mb-2">📦</span>
      <p className="text-sm">Widget: {config.type || 'Unknown'}</p>
      <p className="text-xs mt-1">Coming soon...</p>
    </div>
  );
}
```

### 5. Dashboard Grid Component

#### src/components/layout/DashboardGrid.jsx:
```jsx
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
```

### 6. Add Widget Modal

#### src/components/layout/AddWidgetModal.jsx:
```jsx
import { useState } from 'react';
import { getAvailableWidgets } from '../widgets/widgetRegistry';

export default function AddWidgetModal({ isOpen, onClose, onAdd }) {
  const [selectedType, setSelectedType] = useState(null);
  const availableWidgets = getAvailableWidgets();

  if (!isOpen) return null;

  const handleAdd = () => {
    if (selectedType) {
      onAdd(selectedType);
      setSelectedType(null);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add Widget
          </h2>
        </div>

        <div className="p-4 overflow-y-auto max-h-96">
          <div className="grid gap-2">
            {availableWidgets.map((widget) => (
              <button
                key={widget.type}
                onClick={() => setSelectedType(widget.type)}
                className={`p-3 text-left rounded-lg border-2 transition-colors ${
                  selectedType === widget.type
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="font-medium text-gray-900 dark:text-white">
                  {widget.name}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {widget.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleAdd}
            disabled={!selectedType}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Widget
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 7. Dashboard Header

#### src/components/layout/DashboardHeader.jsx:
```jsx
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

export default function DashboardHeader({ isEditing, onToggleEdit, onAddWidget }) {
  const { user, logout } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <header className="bg-white dark:bg-gray-800 shadow sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          Personal Dash
        </h1>

        <div className="flex items-center gap-2">
          {isEditing && (
            <button
              onClick={onAddWidget}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Widget
            </button>
          )}

          <button
            onClick={onToggleEdit}
            className={`px-3 py-1.5 text-sm rounded-md ${
              isEditing
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {isEditing ? 'Done' : 'Edit'}
          </button>

          <button
            onClick={toggleDarkMode}
            className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
            title={darkMode ? 'Light mode' : 'Dark mode'}
          >
            {darkMode ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-400 hidden sm:inline">
              {user?.display_name || user?.email}
            </span>
            <button
              onClick={logout}
              className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md"
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
```

### 8. Dashboard Hook for State Management

#### src/hooks/useDashboard.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { getWidget } from '../components/widgets/widgetRegistry';

export function useDashboard() {
  const [widgets, setWidgets] = useState([]);
  const [layout, setLayout] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Load dashboard from API
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/dashboard/layout');
      setWidgets(response.data.widgets || []);
      setLayout(response.data.layout || []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      // Use default empty state
      setWidgets([]);
      setLayout([]);
    } finally {
      setLoading(false);
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

    const newLayoutItem = {
      i: id,
      x: 0,
      y: Infinity, // Place at bottom
      w: widgetDef.defaultSize.w,
      h: widgetDef.defaultSize.h,
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

  useEffect(() => {
    loadDashboard();
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
    reload: loadDashboard
  };
}
```

### 9. Updated Dashboard Page

#### src/pages/DashboardPage.jsx:
```jsx
import { useState } from 'react';
import DashboardHeader from '../components/layout/DashboardHeader';
import DashboardGrid from '../components/layout/DashboardGrid';
import AddWidgetModal from '../components/layout/AddWidgetModal';
import { useDashboard } from '../hooks/useDashboard';

export default function DashboardPage() {
  const [isEditing, setIsEditing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

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
    // TODO: Open widget settings modal
    console.log('Settings for widget:', widgetId);
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
            <div className="text-6xl mb-4">📊</div>
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
    </div>
  );
}
```

### 10. Update App.jsx with ThemeProvider

#### src/App.jsx:
```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DashboardPage from './pages/DashboardPage';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
```

### 11. Backend Dashboard Endpoints

#### app/api/v1/endpoints/dashboard.py:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.widget import DashboardLayout
from pydantic import BaseModel
from typing import List, Any, Optional

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

class LayoutItem(BaseModel):
    i: str
    x: int
    y: int
    w: int
    h: int
    minW: Optional[int] = None
    minH: Optional[int] = None
    maxW: Optional[int] = None
    maxH: Optional[int] = None

class WidgetItem(BaseModel):
    id: str
    type: str
    config: dict = {}

class DashboardData(BaseModel):
    widgets: List[WidgetItem]
    layout: List[LayoutItem]

@router.get("/layout", response_model=DashboardData)
def get_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's dashboard layout and widgets."""
    dashboard = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).first()

    if not dashboard:
        return DashboardData(widgets=[], layout=[])

    return DashboardData(
        widgets=dashboard.layout.get("widgets", []),
        layout=dashboard.layout.get("layout", [])
    )

@router.put("/layout", response_model=DashboardData)
def save_dashboard_layout(
    data: DashboardData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user's dashboard layout and widgets."""
    dashboard = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).first()

    layout_data = {
        "widgets": [w.dict() for w in data.widgets],
        "layout": [l.dict() for l in data.layout]
    }

    if dashboard:
        dashboard.layout = layout_data
    else:
        dashboard = DashboardLayout(
            user_id=current_user.id,
            layout=layout_data
        )
        db.add(dashboard)

    db.commit()
    db.refresh(dashboard)

    return data
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
```

### 12. Add Custom CSS for Grid

#### src/styles/grid.css:
```css
.react-grid-item.react-grid-placeholder {
  background: rgb(59, 130, 246);
  opacity: 0.2;
  border-radius: 0.5rem;
}

.react-grid-item > .react-resizable-handle {
  background: none;
}

.react-grid-item > .react-resizable-handle::after {
  content: "";
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 8px;
  height: 8px;
  border-right: 2px solid rgba(0, 0, 0, 0.3);
  border-bottom: 2px solid rgba(0, 0, 0, 0.3);
}

.dark .react-grid-item > .react-resizable-handle::after {
  border-color: rgba(255, 255, 255, 0.3);
}
```

#### Import in src/main.jsx:
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';
import './styles/grid.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

## Acceptance Criteria
- [ ] Dashboard displays with header and grid area
- [ ] Dark mode toggle works and persists
- [ ] Edit mode enables drag-and-drop and resize
- [ ] Add Widget modal shows available widgets
- [ ] Widgets can be added to dashboard
- [ ] Widgets can be removed in edit mode
- [ ] Layout persists to backend API
- [ ] Empty state shows when no widgets
- [ ] Mobile responsive layout

## Estimated Time
4-5 hours

## Next Task
Task 006: Weather Widget
