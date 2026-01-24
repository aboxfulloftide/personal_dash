# Task 017: Dashboard Layout & Polish

## Objective
Finalize the dashboard with drag-and-drop widget layout, responsive design, dark mode, and overall UI polish.

## Prerequisites
- All widget tasks completed (010-016)
- Task 005 completed (Frontend Foundation)
- Task 006 completed (Widget Framework)

## Features
- Drag-and-drop widget grid layout
- Widget resize capability
- Layout persistence per user
- Responsive breakpoints (desktop/tablet/mobile)
- Dark mode toggle with persistence
- Loading states and error boundaries
- Smooth animations and transitions
- Keyboard accessibility

## Deliverables

### 1. Layout Configuration Model

#### backend/app/models/layout.py:
```python
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Grid layout configuration
    # Format: [{ "widget_id": "weather", "x": 0, "y": 0, "w": 2, "h": 2 }, ...]
    layout = Column(JSON, default=list)

    # Breakpoint-specific layouts
    layout_md = Column(JSON, nullable=True)  # Tablet
    layout_sm = Column(JSON, nullable=True)  # Mobile

    # Theme preference
    theme = Column(String(20), default="light")  # light, dark, system

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="dashboard_layout")
```

### 2. Layout API Endpoints

#### backend/app/api/v1/layout.py:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.layout import DashboardLayout
from app.schemas.layout import LayoutUpdate, LayoutResponse, WidgetPosition
from app.api.deps import get_current_user

router = APIRouter(prefix="/layout", tags=["layout"])

# Default widget layout
DEFAULT_LAYOUT = [
    {"widget_id": "server_monitor", "x": 0, "y": 0, "w": 4, "h": 3},
    {"widget_id": "weather", "x": 4, "y": 0, "w": 2, "h": 2},
    {"widget_id": "calendar", "x": 6, "y": 0, "w": 3, "h": 3},
    {"widget_id": "package_tracking", "x": 9, "y": 0, "w": 3, "h": 3},
    {"widget_id": "stocks", "x": 0, "y": 3, "w": 3, "h": 2},
    {"widget_id": "crypto", "x": 3, "y": 3, "w": 3, "h": 2},
    {"widget_id": "news", "x": 6, "y": 3, "w": 3, "h": 3},
    {"widget_id": "fitness", "x": 9, "y": 3, "w": 3, "h": 3},
]


@router.get("", response_model=LayoutResponse)
async def get_layout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user dashboard layout."""
    layout = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).first()

    if not layout:
        # Create default layout
        layout = DashboardLayout(
            user_id=current_user.id,
            layout=DEFAULT_LAYOUT,
            theme="system"
        )
        db.add(layout)
        db.commit()
        db.refresh(layout)

    return layout


@router.put("", response_model=LayoutResponse)
async def update_layout(
    data: LayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user dashboard layout."""
    layout = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).first()

    if not layout:
        layout = DashboardLayout(user_id=current_user.id)
        db.add(layout)

    if data.layout is not None:
        layout.layout = [w.dict() for w in data.layout]
    if data.layout_md is not None:
        layout.layout_md = [w.dict() for w in data.layout_md]
    if data.layout_sm is not None:
        layout.layout_sm = [w.dict() for w in data.layout_sm]
    if data.theme is not None:
        layout.theme = data.theme

    db.commit()
    db.refresh(layout)
    return layout


@router.post("/reset", response_model=LayoutResponse)
async def reset_layout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset layout to default."""
    layout = db.query(DashboardLayout).filter(
        DashboardLayout.user_id == current_user.id
    ).first()

    if layout:
        layout.layout = DEFAULT_LAYOUT
        layout.layout_md = None
        layout.layout_sm = None
        db.commit()
        db.refresh(layout)
    else:
        layout = DashboardLayout(
            user_id=current_user.id,
            layout=DEFAULT_LAYOUT
        )
        db.add(layout)
        db.commit()
        db.refresh(layout)

    return layout
```

### 3. Layout Schemas

#### backend/app/schemas/layout.py:
```python
from pydantic import BaseModel
from typing import List, Optional


class WidgetPosition(BaseModel):
    widget_id: str
    x: int
    y: int
    w: int
    h: int


class LayoutUpdate(BaseModel):
    layout: Optional[List[WidgetPosition]] = None
    layout_md: Optional[List[WidgetPosition]] = None
    layout_sm: Optional[List[WidgetPosition]] = None
    theme: Optional[str] = None


class LayoutResponse(BaseModel):
    id: int
    layout: List[dict]
    layout_md: Optional[List[dict]]
    layout_sm: Optional[List[dict]]
    theme: str

    class Config:
        from_attributes = True
```

### 4. Dashboard Grid Component

#### frontend/src/components/Dashboard/DashboardGrid.jsx:
```jsx
import React, { useState, useEffect, useCallback } from 'react';
import GridLayout from 'react-grid-layout';
import { useLayout } from '../../hooks/useLayout';
import { useTheme } from '../../contexts/ThemeContext';
import WidgetWrapper from './WidgetWrapper';
import DashboardHeader from './DashboardHeader';

// Widget imports
import ServerMonitorWidget from '../widgets/ServerMonitorWidget';
import WeatherWidget from '../widgets/WeatherWidget';
import CalendarWidget from '../widgets/CalendarWidget';
import PackageTrackingWidget from '../widgets/PackageTrackingWidget';
import StockWidget from '../widgets/StockWidget';
import CryptoWidget from '../widgets/CryptoWidget';
import NewsWidget from '../widgets/NewsWidget';
import FitnessWidget from '../widgets/FitnessWidget';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const WIDGET_COMPONENTS = {
  server_monitor: ServerMonitorWidget,
  weather: WeatherWidget,
  calendar: CalendarWidget,
  package_tracking: PackageTrackingWidget,
  stocks: StockWidget,
  crypto: CryptoWidget,
  news: NewsWidget,
  fitness: FitnessWidget,
};

const WIDGET_TITLES = {
  server_monitor: 'Server Monitor',
  weather: 'Weather',
  calendar: 'Calendar',
  package_tracking: 'Package Tracking',
  stocks: 'Stocks',
  crypto: 'Crypto',
  news: 'News',
  fitness: 'Fitness',
};

// Grid configuration
const COLS = { lg: 12, md: 8, sm: 4, xs: 2 };
const BREAKPOINTS = { lg: 1200, md: 996, sm: 768, xs: 480 };
const ROW_HEIGHT = 100;
const MARGIN = [16, 16];

export default function DashboardGrid() {
  const { layout, loading, updateLayout, resetLayout } = useLayout();
  const { theme } = useTheme();
  const [currentBreakpoint, setCurrentBreakpoint] = useState('lg');
  const [isEditing, setIsEditing] = useState(false);
  const [containerWidth, setContainerWidth] = useState(1200);

  // Calculate container width
  useEffect(() => {
    const updateWidth = () => {
      const container = document.getElementById('dashboard-container');
      if (container) {
        setContainerWidth(container.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Determine breakpoint
  useEffect(() => {
    const width = window.innerWidth;
    if (width >= BREAKPOINTS.lg) setCurrentBreakpoint('lg');
    else if (width >= BREAKPOINTS.md) setCurrentBreakpoint('md');
    else if (width >= BREAKPOINTS.sm) setCurrentBreakpoint('sm');
    else setCurrentBreakpoint('xs');
  }, [containerWidth]);

  const handleLayoutChange = useCallback((newLayout) => {
    if (!isEditing) return;

    const formattedLayout = newLayout.map(item => ({
      widget_id: item.i,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
    }));

    updateLayout({ layout: formattedLayout });
  }, [isEditing, updateLayout]);

  const getGridLayout = () => {
    if (!layout?.layout) return [];

    return layout.layout.map(item => ({
      i: item.widget_id,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      minW: 2,
      minH: 2,
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div 
      id="dashboard-container"
      className={`min-h-screen transition-colors duration-300 ${
        theme === 'dark' ? 'bg-gray-900' : 'bg-gray-100'
      }`}
    >
      <DashboardHeader 
        isEditing={isEditing}
        onToggleEdit={() => setIsEditing(!isEditing)}
        onReset={resetLayout}
      />

      <div className="p-4">
        {isEditing && (
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-sm text-blue-700 dark:text-blue-300">
            <strong>Edit Mode:</strong> Drag widgets to reposition. Drag corners to resize. 
            Click "Done" when finished.
          </div>
        )}

        <GridLayout
          className="layout"
          layout={getGridLayout()}
          cols={COLS[currentBreakpoint] || 12}
          rowHeight={ROW_HEIGHT}
          width={containerWidth - 32}
          margin={MARGIN}
          isDraggable={isEditing}
          isResizable={isEditing}
          onLayoutChange={handleLayoutChange}
          draggableHandle=".widget-drag-handle"
          useCSSTransforms={true}
        >
          {layout?.layout?.map(item => {
            const WidgetComponent = WIDGET_COMPONENTS[item.widget_id];

            if (!WidgetComponent) return null;

            return (
              <div key={item.widget_id}>
                <WidgetWrapper
                  title={WIDGET_TITLES[item.widget_id]}
                  isEditing={isEditing}
                  widgetId={item.widget_id}
                >
                  <WidgetComponent config={{}} />
                </WidgetWrapper>
              </div>
            );
          })}
        </GridLayout>
      </div>
    </div>
  );
}
```

### 5. Widget Wrapper Component

#### frontend/src/components/Dashboard/WidgetWrapper.jsx:
```jsx
import React, { useState } from 'react';
import { GripVertical, Maximize2, Minimize2, RefreshCw, X } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

export default function WidgetWrapper({ 
  title, 
  children, 
  isEditing, 
  widgetId,
  onRemove,
  onRefresh 
}) {
  const { theme } = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (onRefresh) {
      setIsRefreshing(true);
      await onRefresh();
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const baseClasses = `
    h-full rounded-xl shadow-sm overflow-hidden
    transition-all duration-300 ease-in-out
    ${theme === 'dark' 
      ? 'bg-gray-800 border border-gray-700' 
      : 'bg-white border border-gray-200'
    }
    ${isEditing ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}
    ${isExpanded ? 'fixed inset-4 z-50' : ''}
  `;

  return (
    <>
      {/* Backdrop for expanded view */}
      {isExpanded && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsExpanded(false)}
        />
      )}

      <div className={baseClasses}>
        {/* Header */}
        <div className={`
          flex items-center justify-between px-3 py-2 border-b
          ${theme === 'dark' ? 'border-gray-700' : 'border-gray-100'}
        `}>
          <div className="flex items-center gap-2">
            {isEditing && (
              <div className="widget-drag-handle cursor-move p-1 -ml-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                <GripVertical className="w-4 h-4 text-gray-400" />
              </div>
            )}
            <h3 className={`font-medium text-sm ${
              theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
            }`}>
              {title}
            </h3>
          </div>

          <div className="flex items-center gap-1">
            {onRefresh && (
              <button
                onClick={handleRefresh}
                className={`p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  isRefreshing ? 'animate-spin' : ''
                }`}
                title="Refresh"
              >
                <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
              </button>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              title={isExpanded ? 'Minimize' : 'Expand'}
            >
              {isExpanded ? (
                <Minimize2 className="w-3.5 h-3.5 text-gray-400" />
              ) : (
                <Maximize2 className="w-3.5 h-3.5 text-gray-400" />
              )}
            </button>

            {isEditing && onRemove && (
              <button
                onClick={onRemove}
                className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30"
                title="Remove Widget"
              >
                <X className="w-3.5 h-3.5 text-red-400" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className={`p-3 h-[calc(100%-44px)] overflow-auto ${
          theme === 'dark' ? 'text-gray-200' : 'text-gray-800'
        }`}>
          <ErrorBoundary widgetId={widgetId}>
            {children}
          </ErrorBoundary>
        </div>
      </div>
    </>
  );
}

// Error Boundary for widgets
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`Widget ${this.props.widgetId} error:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex items-center justify-center text-center p-4">
          <div>
            <p className="text-red-500 mb-2">Something went wrong</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="text-sm text-blue-500 hover:underline"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 6. Dashboard Header

#### frontend/src/components/Dashboard/DashboardHeader.jsx:
```jsx
import React from 'react';
import { Moon, Sun, Monitor, Edit3, Check, RotateCcw, LogOut, User } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

export default function DashboardHeader({ isEditing, onToggleEdit, onReset }) {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();

  const themeOptions = [
    { value: 'light', icon: Sun, label: 'Light' },
    { value: 'dark', icon: Moon, label: 'Dark' },
    { value: 'system', icon: Monitor, label: 'System' },
  ];

  return (
    <header className={`
      sticky top-0 z-30 px-4 py-3 border-b backdrop-blur-sm
      ${theme === 'dark' 
        ? 'bg-gray-900/90 border-gray-700' 
        : 'bg-white/90 border-gray-200'
      }
    `}>
      <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <h1 className={`text-xl font-bold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            Personal Dash
          </h1>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <div className={`
            flex rounded-lg p-1
            ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-100'}
          `}>
            {themeOptions.map(({ value, icon: Icon, label }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={`
                  p-2 rounded-md transition-colors
                  ${theme === value 
                    ? 'bg-blue-500 text-white' 
                    : theme === 'dark'
                      ? 'text-gray-400 hover:text-white'
                      : 'text-gray-500 hover:text-gray-900'
                  }
                `}
                title={label}
              >
                <Icon className="w-4 h-4" />
              </button>
            ))}
          </div>

          {/* Edit Layout Button */}
          <button
            onClick={onToggleEdit}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
              ${isEditing
                ? 'bg-green-500 text-white hover:bg-green-600'
                : theme === 'dark'
                  ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {isEditing ? (
              <>
                <Check className="w-4 h-4" />
                <span className="text-sm">Done</span>
              </>
            ) : (
              <>
                <Edit3 className="w-4 h-4" />
                <span className="text-sm hidden sm:inline">Edit Layout</span>
              </>
            )}
          </button>

          {/* Reset Layout */}
          {isEditing && (
            <button
              onClick={onReset}
              className={`
                p-2 rounded-lg transition-colors
                ${theme === 'dark'
                  ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
              title="Reset to Default Layout"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}

          {/* User Menu */}
          <div className="relative group">
            <button className={`
              flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
              ${theme === 'dark'
                ? 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}>
              <User className="w-4 h-4" />
              <span className="text-sm hidden sm:inline">{user?.username}</span>
            </button>

            {/* Dropdown */}
            <div className={`
              absolute right-0 mt-2 w-48 rounded-lg shadow-lg py-1 hidden group-hover:block
              ${theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border'}
            `}>
              <button
                onClick={logout}
                className={`
                  w-full flex items-center gap-2 px-4 py-2 text-sm
                  ${theme === 'dark'
                    ? 'text-gray-300 hover:bg-gray-700'
                    : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
```

### 7. Theme Context

#### frontend/src/contexts/ThemeContext.jsx:
```jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState('system');
  const [resolvedTheme, setResolvedTheme] = useState('light');

  // Load saved theme
  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'system';
    setThemeState(saved);
  }, []);

  // Resolve system theme
  useEffect(() => {
    const updateResolvedTheme = () => {
      if (theme === 'system') {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setResolvedTheme(isDark ? 'dark' : 'light');
      } else {
        setResolvedTheme(theme);
      }
    };

    updateResolvedTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', updateResolvedTheme);

    return () => mediaQuery.removeEventListener('change', updateResolvedTheme);
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  const setTheme = (newTheme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  return (
    <ThemeContext.Provider value={{ 
      theme: resolvedTheme, 
      themePreference: theme,
      setTheme 
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

### 8. Layout Hook

#### frontend/src/hooks/useLayout.js:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useLayout() {
  const [layout, setLayout] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchLayout = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/layout');
      setLayout(response.data);
    } catch (err) {
      console.error('Failed to fetch layout:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLayout();
  }, [fetchLayout]);

  const updateLayout = useCallback(async (data) => {
    try {
      const response = await api.put('/layout', data);
      setLayout(response.data);
    } catch (err) {
      console.error('Failed to update layout:', err);
    }
  }, []);

  const resetLayout = useCallback(async () => {
    try {
      const response = await api.post('/layout/reset');
      setLayout(response.data);
    } catch (err) {
      console.error('Failed to reset layout:', err);
    }
  }, []);

  return {
    layout,
    loading,
    fetchLayout,
    updateLayout,
    resetLayout
  };
}
```

### 9. Global Styles

#### frontend/src/styles/globals.css:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.dark ::-webkit-scrollbar-thumb {
  background: #475569;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* Smooth transitions */
* {
  transition-property: background-color, border-color, color;
  transition-duration: 150ms;
  transition-timing-function: ease-in-out;
}

/* Grid layout animations */
.react-grid-item {
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.react-grid-item.react-grid-placeholder {
  background: #3b82f6 !important;
  opacity: 0.2;
  border-radius: 12px;
}

.react-grid-item.resizing,
.react-grid-item.react-draggable-dragging {
  z-index: 100;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Focus styles for accessibility */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Loading skeleton */
.skeleton {
  background: linear-gradient(
    90deg,
    #f1f5f9 25%,
    #e2e8f0 50%,
    #f1f5f9 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.dark .skeleton {
  background: linear-gradient(
    90deg,
    #1e293b 25%,
    #334155 50%,
    #1e293b 75%
  );
  background-size: 200% 100%;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Widget card hover effect */
.widget-card {
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.widget-card:hover {
  transform: translateY(-2px);
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .react-grid-layout {
    margin: 0 -8px;
  }

  .react-grid-item {
    padding: 0 8px;
  }
}
```

### 10. Tailwind Dark Mode Config

#### frontend/tailwind.config.js:
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom color palette if needed
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-in-out',
        'slide-up': 'slideUp 200ms ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

### 11. App Entry Point Update

#### frontend/src/App.jsx:
```jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import DashboardGrid from './components/Dashboard/DashboardGrid';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return !isAuthenticated ? children : <Navigate to="/" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemeProvider>
          <Routes>
            <Route 
              path="/" 
              element={
                <PrivateRoute>
                  <DashboardGrid />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              } 
            />
            <Route 
              path="/register" 
              element={
                <PublicRoute>
                  <RegisterPage />
                </PublicRoute>
              } 
            />
            <Route 
              path="/forgot-password" 
              element={
                <PublicRoute>
                  <ForgotPasswordPage />
                </PublicRoute>
              } 
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

## New Dependencies

### Frontend (package.json additions):
```json
{
  "dependencies": {
    "react-grid-layout": "^1.4.4"
  }
}
```

## Unit Tests

### tests/test_layout_api.py:
```python
import pytest
from fastapi.testclient import TestClient


class TestLayoutAPI:
    def test_get_layout_creates_default(self, client, auth_headers):
        response = client.get("/api/v1/layout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "layout" in data
        assert len(data["layout"]) > 0

    def test_update_layout(self, client, auth_headers):
        new_layout = [
            {"widget_id": "weather", "x": 0, "y": 0, "w": 3, "h": 2}
        ]
        response = client.put(
            "/api/v1/layout",
            json={"layout": new_layout},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["layout"]) == 1
        assert data["layout"][0]["widget_id"] == "weather"

    def test_update_theme(self, client, auth_headers):
        response = client.put(
            "/api/v1/layout",
            json={"theme": "dark"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"

    def test_reset_layout(self, client, auth_headers):
        # First update
        client.put(
            "/api/v1/layout",
            json={"layout": []},
            headers=auth_headers
        )

        # Then reset
        response = client.post("/api/v1/layout/reset", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["layout"]) > 0
```

## Acceptance Criteria
- [ ] Drag-and-drop widget repositioning works
- [ ] Widget resizing works
- [ ] Layout persists after page refresh
- [ ] Layout saves to database per user
- [ ] Dark mode toggle works
- [ ] Theme preference persists
- [ ] System theme detection works
- [ ] Responsive layout on mobile/tablet
- [ ] Edit mode clearly indicated
- [ ] Reset to default layout works
- [ ] Error boundaries catch widget errors
- [ ] Loading states display properly
- [ ] Smooth animations on interactions
- [ ] Keyboard accessible (tab navigation)
- [ ] Widget expand/minimize works

## Performance Considerations
- Debounce layout save (do not save on every pixel move)
- Use CSS transforms for animations (GPU accelerated)
- Lazy load widget content
- Memoize widget components

## Accessibility Checklist
- [ ] Focus indicators visible
- [ ] Keyboard navigation works
- [ ] Screen reader labels present
- [ ] Color contrast meets WCAG AA
- [ ] Reduced motion respected

## Estimated Time
3-4 hours

## Final Integration Notes
After this task, the dashboard should be fully functional with:
- All 8 widgets working
- Customizable layout
- Dark/light/system themes
- Responsive design
- User authentication
- Data persistence

## Deployment Checklist
- [ ] Run all unit tests
- [ ] Build frontend for production
- [ ] Configure Nginx for static files
- [ ] Set up systemd service for backend
- [ ] Configure MySQL database
- [ ] Set environment variables
- [ ] Enable HTTPS
- [ ] Test all widgets end-to-end
