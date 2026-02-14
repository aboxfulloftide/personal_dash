# Personal Dash - Project Plan

## Overview
Personal Dash is a self-hosted, multi-user personal dashboard application that aggregates various data sources into customizable widgets. Built with a plugin architecture for easy widget additions.

> 📌 **Widget Development:** To add alerts to your widgets, see [WIDGET_ALERTS.md](WIDGET_ALERTS.md) for complete guide and API reference.

## Tech Stack
- **Frontend:** React with Vite, Tailwind CSS
- **Backend:** Python with FastAPI
- **Database:** MySQL
- **Authentication:** JWT with refresh tokens
- **Deployment:** Self-hosted Linux (systemd + Nginx)

## Core Features
- Multi-user support with JWT authentication
- Drag-and-drop customizable widget grid
- **Widget alert system** - Priority notifications with visual indicators (see [WIDGET_ALERTS.md](WIDGET_ALERTS.md))
- Dark mode support
- Mobile responsive design
- Plugin/widget architecture for extensibility

## Widget List (Priority Order)
1. **System/Server Monitoring** - Custom Python agent, Docker stats, Wake-on-LAN
2. **Package Tracking** - USPS, UPS, FedEx, Amazon (manual entry + email parsing)
3. **Stock Ticker** - Real-time stock prices (free APIs)
4. **Crypto Prices** - Cryptocurrency tracking (free APIs)
5. **Weather** - Current conditions and forecast (free APIs)
6. **Calendar** - Google Calendar integration
7. **News Headlines** - RSS/News API aggregation
8. **Fitness Stats** - Body weight tracking (manual entry)
9. **Smart Home** - Home Assistant integration
10. **Picture Frame** - Digital photo frame displaying images from a directory (slideshow or random)

## Architecture Principles
- Monorepo structure
- API versioning (/api/v1/)
- Widget configurations stored in DB per user
- Rate limiting with intelligent caching
- Unit tests for all features

## Deployment Strategy
- Backend: FastAPI via systemd
- Frontend: Static files via Nginx
- MySQL: Direct installation
- Monitoring agents: Python scripts via systemd on remote servers

## Project Structure
```
personal-dash/
├── frontend/           # React application
├── backend/            # FastAPI application
├── agent/              # Server monitoring agent
├── docs/               # Documentation
│   ├── PROJECT_PLAN.md
│   ├── TECH_SPECS.md
│   ├── WIDGET_ALERTS.md  # Widget alert system guide
│   ├── BACKLOG.md
│   └── tasks/          # Individual task files
└── tests/              # Test suites
```

## Task Breakdown

> **Note:** Mark tasks as completed by changing `[ ]` to `[x]` when done.

- [x] 1. Project Setup
- [x] 2. Database Models & Migrations
- [x] 3. Authentication System
- [x] 4. Frontend Authentication UI
- [x] 5. Dashboard Layout & Widget Grid
- [x] 6. Widget Base Architecture
- [x] 7. Server Monitoring Agent
- [x] 8. Server Monitoring API
- [x] 9. Server Monitoring Dashboard Widget
- [x] 10. Package Tracking Backend
- [x] 11. Package Tracking Widget
- [x] 12. Stock Ticker Widget
- [x] 13. Crypto Widget
- [x] 14. Weather Widget
  - [x] Phase 1: Extended Hourly Forecast (clickable, external links, through midnight)
  - [x] Phase 2: Sunrise/Sunset Times (with visual progression bar)
  - [x] Phase 3: Weather Radar (RainViewer API, animated, expandable)
- [x] 15. Calendar Widget (Google Calendar/ICS support)
- [x] 16. News Headlines Widget (RSS with keyword filtering)
- [x] 17. Network Status Widget (Ping monitoring with custom targets)
- [x] 18. Widget Alert System (Priority notifications - see [WIDGET_ALERTS.md](WIDGET_ALERTS.md))
- [x] 19. Email Integration for Package Tracking (IMAP auto-scan)
- [ ] 20. Additional Widgets (Fitness, Smart Home, Picture Frame)
- [ ] 21. Deployment & Documentation

## Recent Enhancements

### Calendar Widget - Smart Event Display (Completed - 2026-02-13)
**Intelligent Auto-View Selection**
- Progressive fallback logic: Today → Week → Month → empty state
- Automatically selects the first view with events (no more hunting)
- Event counts displayed in each tab (e.g., "Today: 3", "Week: 12")
- Smart View indicator shows which view was auto-selected and why
- Manual override support (user can click tabs, resets on month navigation)
- Single API call optimization (fetches month, filters client-side)

**Bug Fixes**
- Fixed date range filtering to correctly exclude end boundary
- Events on Feb 14 no longer appear in Feb 13's "today" view
- Timezone handling now uses local server time (not UTC)

**Technical Implementation:**
- Backend: Added `auto_fallback`, event count metadata, smart selection logic
- Frontend: Auto-sync view, event counts in tabs, Smart View indicator
- Performance: 10-minute cache, instant view switching, O(n) counting

**Files Modified:**
- `backend/app/api/v1/endpoints/calendar.py` - Smart selection + date fix
- `frontend/src/components/widgets/CalendarWidget.jsx` - Auto-view sync + UI

**Documentation:**
- `CALENDAR_SMART_VIEW_IMPLEMENTATION.md` - Complete implementation guide

---

### Stock/Crypto Portfolio Value Graph & Watchlist (Completed - 2026-02-13)
**Portfolio Performance Visualization**
- Added historical portfolio value graphs to Stock Ticker and Crypto widgets
- 90-day portfolio history with automatic daily/weekly aggregation
- Color-coded visualization: green for gains, red for losses
- Summary stats: current value, starting value, gain/loss percentage
- Expandable section with lazy loading (only fetches when opened)
- Manual refresh button for on-demand updates

**Portfolio vs Watchlist Tracking**
- Holdings can now be marked as "Portfolio" (💼) or "Watchlist" (👁️)
- Portfolio holdings: owned stocks/crypto included in value calculations
- Watchlist items: price tracking only, excluded from calculations
- Visual indicators and separate counts in widget header
- Type selection in Add modal with toggle buttons
- Automatic migration of existing holdings to "portfolio" type

**Technical Details**
- Backend: New API endpoints for portfolio history calculation
- Frontend: Reusable PortfolioGraph component using Recharts
- Uses existing historical price data (no new tables needed)
- Forward-fill logic handles missing data points

### Network Status Widget - Speed Tests (Completed - 2026-02-13)
**Phase 3: Network Speed Tests**
- On-demand bandwidth testing using speedtest-cli (download/upload speeds)
- Rate limiting (15 minutes minimum between tests)
- Historical tracking with visualization (24h/7d/30d views)
- Speed test result card with server information
- Dual-line chart (download=green, upload=blue)
- Automatic cleanup of old test results (90 days retention)

**Technical Implementation:**
- Backend:
  - `speed_test_results` database table with composite index
  - Speed test utility wrapping speedtest-cli library
  - 3 new API endpoints (run test, get history, get stats)
  - CRUD operations with rate limiting check
  - Daily cleanup scheduler job
- Frontend:
  - "Network Speed" section in NetworkStatusWidget
  - Progress indicator during test (30-60s)
  - Expandable history section with Recharts visualization
  - Time range selector (24h/7d/30d)
  - Rate limiting UI with error handling

**Files Modified:**
- `backend/requirements.txt` - Added speedtest-cli==2.1.3
- `backend/app/models/network.py` - SpeedTestResult model
- `backend/app/utils/speedtest_utils.py` - NEW FILE
- `backend/app/crud/speedtest.py` - NEW FILE
- `backend/app/schemas/network.py` - 5 new schemas
- `backend/app/api/v1/endpoints/network.py` - 3 new endpoints
- `backend/app/core/scheduler.py` - Cleanup task
- `backend/alembic/versions/*_add_speed_test_results_table.py` - Migration
- `frontend/src/components/widgets/NetworkStatusWidget.jsx` - Speed test UI

---

### Package Cleanup Scheduler Fix (Completed - 2026-02-13)
**Improved Cleanup Timing**
- Email scanner runs every 30 minutes (faster package detection and delivery marking)
- Cleanup task runs every 30 minutes (removes delivered packages within 30 min of midnight)
- Added immediate cleanup run on backend startup (catches packages from overnight)
- Ensures delivered packages are removed promptly at midnight the next day

**Files Modified:**
- `backend/app/core/scheduler.py` - Set both tasks to 30-minute intervals
- `backend/app/main.py` - Added startup cleanup task

**Root Cause:** Original 6-hour interval meant packages could wait many hours after midnight before removal. 30-minute interval provides near-real-time cleanup and email scanning.

---

### Dashboard UX Improvements (Completed - 2026-02-12)
**Silent Background Refresh**
- Background polling for alerts without loading states or flashing
- Polling interval: 60 seconds (previously caused jarring reloads)
- Keeps current data visible while fetching updates
- Smooth UX for users with many widgets

**Files Modified:**
- `frontend/src/hooks/useDashboard.js` - Added silent mode for background refreshes

---

### Package Tracker Enhancements (Completed - 2026-02-12)
**Delivery Detection Improvements**
- Fixed duplicate package handling (marks all duplicates as delivered)
- Enhanced delivery confirmation detection from emails
- Debug logging for troubleshooting delivery matching
- Midnight cleanup instead of 24-hour removal

**Files Modified:**
- `backend/app/crud/package.py` - Duplicate handling, debug logging
- `backend/app/core/scheduler.py` - Midnight cleanup logic, timing logs

---

### Widget Alert System (Completed - 2026-02-12)
**Overview:** Framework allowing any widget to display priority notifications by moving to top of dashboard until acknowledged.

**Features:**
- Three severity levels: Critical (🔴), Warning (⚠️), Info (ℹ️)
- Automatic widget repositioning to top of dashboard
- Pulsing colored borders based on severity
- Alert banner with message and acknowledge button
- Auto-refresh every 30 seconds to detect new alerts
- Position restoration after acknowledgment
- Multiple alert support with priority sorting

**Implementation:**
- Backend API endpoints: `POST /widgets/{id}/alert` and `POST /widgets/{id}/acknowledge`
- Frontend components: AlertBadge, AlertBanner, AcknowledgeButton
- Automatic layout management in DashboardGrid
- Test script for triggering/managing alerts

**Documentation:** See [WIDGET_ALERTS.md](WIDGET_ALERTS.md) for complete guide

---

### Weather Widget Enhancements (Completed)
**Phase 1: Extended Hourly Forecast**
- Hourly forecast shows every 2 hours through midnight (including next day's 12 AM)
- Each hourly item is clickable and opens external detailed forecast in new tab
- 4 external forecast providers: Windy.com, Weather Underground, NWS, OpenWeatherMap
- Provider selectable in widget settings
- Visual midnight indicator (left border)

**Phase 2: Sunrise/Sunset Times**
- Displays sunrise 🌅 and sunset 🌆 times in "6:45 AM" format
- Visual progression bar showing sun's current position through the day
- Animated sun indicator (yellow circle) that moves along the bar
- Dynamic colors: orange/yellow gradient during day, gray at night

**Phase 3: Weather Radar**
- Integrated RainViewer API for animated precipitation radar (free, no API key)
- Expandable/collapsible radar section (hidden by default)
- Interactive Leaflet.js map centered on user's location
- Play/Pause animation controls (shows ~2 hours of radar history)
- Toggle-able in widget settings (show_radar option)

**Additional UX Improvements**
- Widget content is scrollable when overflow occurs (invisible scrollbar)
- Widgets can only be dragged by clicking the header (not content area)
- Drag and resize only work in edit mode (widgets locked when edit is off)

---

## Pending Work - Ranked by Difficulty

> **Note:** Ranked from easiest to hardest. See `docs/BACKLOG.md` for detailed specifications.

### ✅ Recently Completed

1. ~~**News Headlines - Priority keywords with highlighting**~~ ✅
2. ~~**Server Monitor - Track specific processes**~~ ✅
3. ~~**Server Monitor - Monitor mounted drives**~~ ✅
4. ~~**Network Status Widget**~~ ✅ (Phase 1: Ping monitoring, Phase 2: History/Uptime, Phase 3: Speed tests)
5. ~~**Stock & Crypto - Database caching**~~ ✅
6. ~~**Email Integration for Package Tracking**~~ ✅
7. ~~**Widget Alert System**~~ ✅
8. ~~**Stock & Crypto - Portfolio value graph**~~ ✅

### 🟢 Easy (2-5 hours)

1. **Picture Frame widget** (~4-5 hours)
   - Display images from directory (slideshow/random)

2. **Package Tracker - Improve delivery detection** (~3-4 hours)
   - Change from 24-hour removal to next-midnight removal for better visibility

### 🟡 Moderate (5-8 hours)

3. **Fitness Stats widget** (~5-6 hours)
   - Body weight tracking with charts

4. **Weather - Severe weather alerts** (~6-8 hours)
   - Overlay alerts on radar map

5. ~~**Calendar - Smart event display**~~ ✅ **COMPLETED** (2026-02-13, ~3 hours)
   - Progressive fallback: today → week → month with auto-selection

6. **Weather - Moon phase tracker** (~5-6 hours)
   - Display current moon phase with icon and illumination percentage

### 🔴 Complex (8-20+ hours)

8. **Stock & Crypto - Portfolio value graph** (~8-10 hours)
   - Daily/weekly portfolio tracking (requires database caching - ✅ DONE)

9. **Smart Home widget** (~10-15 hours)
   - Home Assistant integration

10. **Deployment & Documentation** (~10-20+ hours)
    - Deployment scripts, systemd services, Nginx config
    - Production deployment guide
