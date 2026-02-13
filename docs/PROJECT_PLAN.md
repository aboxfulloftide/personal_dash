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

### Widget Alert System (Completed)
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
4. ~~**Network Speed & Connection Status widget**~~ ✅ (Phase 1: Ping monitoring)
5. ~~**Stock & Crypto - Database caching**~~ ✅
6. ~~**Email Integration for Package Tracking**~~ ✅
7. ~~**Widget Alert System**~~ ✅

### 🟢 Easy (2-5 hours)

1. **Picture Frame widget** (~4-5 hours)
   - Display images from directory (slideshow/random)

2. **Package Tracker - Improve delivery detection** (~3-4 hours)
   - Change from 24-hour removal to next-midnight removal for better visibility

### 🟡 Moderate (5-8 hours)

3. **Fitness Stats widget** (~5-6 hours)
   - Body weight tracking with charts

4. **Network Status - Speed tests** (~4-6 hours)
   - Add download/upload speed tests (Phase 2 of Network Status widget)
   - Historical speed tracking with graphs

5. **Weather - Severe weather alerts** (~6-8 hours)
   - Overlay alerts on radar map

6. **Calendar - Smart event display** (~6-8 hours)
   - Progressive fallback: current event → next event → today's events → week view

7. **Weather - Moon phase tracker** (~5-6 hours)
   - Display current moon phase with icon and illumination percentage

### 🔴 Complex (8-20+ hours)

8. **Stock & Crypto - Portfolio value graph** (~8-10 hours)
   - Daily/weekly portfolio tracking (requires database caching - ✅ DONE)

9. **Smart Home widget** (~10-15 hours)
   - Home Assistant integration

10. **Deployment & Documentation** (~10-20+ hours)
    - Deployment scripts, systemd services, Nginx config
    - Production deployment guide
