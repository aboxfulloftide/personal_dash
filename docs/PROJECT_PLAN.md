# Personal Dash - Project Plan

## Overview
Personal Dash is a self-hosted, multi-user personal dashboard application that aggregates various data sources into customizable widgets. Built with a plugin architecture for easy widget additions.

## Tech Stack
- **Frontend:** React with Vite, Tailwind CSS
- **Backend:** Python with FastAPI
- **Database:** MySQL
- **Authentication:** JWT with refresh tokens
- **Deployment:** Self-hosted Linux (systemd + Nginx)

## Core Features
- Multi-user support with JWT authentication
- Drag-and-drop customizable widget grid
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
- [ ] 15. Additional Widgets (Calendar, News, Fitness, Smart Home)
- [ ] 16. Email Integration for Package Tracking
- [ ] 17. Deployment & Documentation

## Recent Enhancements

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

### 🟢 Easy (2-5 hours)

1. ~~**News Headlines - Priority keywords with highlighting**~~ ✅ **COMPLETED**
   - Articles with priority keywords are highlighted and bumped to top
   - Shows matched keyword badges with visual indicators

2. **Server Monitor - Track specific processes** (~3-4 hours)
   - Monitor mysql, plex, game servers, etc.

3. **Server Monitor - Monitor mounted drives** (~3-4 hours)
   - Track NAS mounts, external drives status

4. **Picture Frame widget** (~4-5 hours)
   - Display images from directory (slideshow/random)

### 🟡 Moderate (5-8 hours)

5. **Fitness Stats widget** (~5-6 hours)
   - Body weight tracking with charts

6. **Network Speed & Connection Status widget** (~5-7 hours)
   - Run speed tests (download/upload/ping)
   - Monitor connection status
   - Historical speed tracking with graphs

7. **Stock & Crypto - Database caching** (~6-8 hours)
   - Cache API results, fallback when rate limited

8. **Package Tracker - Auto-remove delivered** (~6-8 hours)
   - Auto-remove with email confirmation parsing

9. **Weather - Severe weather alerts** (~6-8 hours)
   - Overlay alerts on radar map

### 🔴 Complex (8-20+ hours)

10. **Stock & Crypto - Portfolio value graph** (~8-10 hours)
    - Daily/weekly portfolio tracking (requires #7 first)

11. **Email Integration for Package Tracking** (~12-15 hours)
    - IMAP + email parsing for multiple carriers

12. **Deployment & Documentation** (~10-20+ hours)
    - Deployment scripts, guides, feature docs
