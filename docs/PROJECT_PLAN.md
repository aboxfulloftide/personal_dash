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
10. **GitHub Activity** - Repository stats and activity

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
1. Project Setup
2. Database Models & Migrations
3. Authentication System
4. Frontend Authentication UI
5. Dashboard Layout & Widget Grid
6. Widget Base Architecture
7. Server Monitoring Agent
8. Server Monitoring API
9. Server Monitoring Dashboard Widget
10. Package Tracking Backend
11. Package Tracking Widget
12. Stock Ticker Widget
13. Crypto Widget
14. Weather Widget
15. Additional Widgets (Calendar, News, Fitness, Smart Home, GitHub)
16. Email Integration for Package Tracking
17. Deployment & Documentation
