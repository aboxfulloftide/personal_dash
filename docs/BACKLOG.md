# Personal Dash - Backlog (Bugs & Enhancements)

> **Note:** This file tracks bugs and enhancement ideas for future work.

---

## Priority Summary

### High Priority (Do Next)
1. **Network Status Widget Phase 2** - Builds on completed Phase 1, adds valuable packet loss and uptime tracking
2. **Stock/Crypto: Portfolio Value Graph** - Now unblocked with database caching complete

### Medium Priority (Soon)
3. **Package Tracker: Auto-remove Delivered** - Quality of life improvement
4. **News: Priority Keywords** - Already partially implemented, needs UI enhancement
5. **Server Monitor: Track Specific Processes** - Already completed, but may need additional features

### Lower Priority (Later)
7. **Weather Widget Enhancements** - Nice to have additions
8. **Network Speed Test Widget** - Separate widget, different from Network Status

---

## Package Tracker

### Enhancements

#### Auto-remove Delivered Packages
**Status:** Not Started
**Priority:** Medium
**Description:**
Currently, packages that are delivered remain in the tracker indefinitely. They should be automatically removed after delivery.

**Proposed Solution:**
1. When a package is marked as delivered, highlight it visually to notify the user
2. Automatically remove the delivered package the next day (24 hours later)
3. Tie delivery confirmation to a separate email notification
   - Watch for delivery confirmation emails with similar subject lines
   - Parse delivery email to confirm package was delivered
   - Update package status accordingly

**Technical Notes:**
- Need to add a "delivered_at" timestamp field to track when package was delivered
- Add a background job or scheduled task to clean up old delivered packages
- Email parser needs to recognize delivery confirmation emails (separate from tracking updates)
- Consider adding a user setting: "Auto-remove delivered after X days" (default: 1 day)

**Related Files:**
- `backend/app/api/v1/endpoints/packages.py`
- `backend/app/models/package.py`
- Email parsing logic (if exists)

---

## Stock Ticker & Crypto Widgets

### Enhancements

#### Portfolio Value Graph
**Status:** Not Started
**Priority:** Medium
**Description:**
Add a graph to Stock and Crypto widgets showing total portfolio value over time.

**Requirements:**
- Track and display total portfolio value (sum of all holdings) over time
- Graph starts from the first day we have stored data
- **Display Mode:**
  - First 30 days: Daily graph (one data point per day)
  - After 30 days: Weekly graph (one data point per week)
- Shows historical performance and trends

**Technical Implementation:**
- Leverage the database cache tables from the caching enhancement above
- Calculate daily total value: `SUM(quantity * price)` for all holdings
- Store daily portfolio snapshots:
  - Table: `portfolio_history` (user_id, date, total_value, widget_type)
  - One record per day per widget type (stock/crypto)
- Frontend graph component (use Chart.js or Recharts):
  - Query last 30 days for daily view
  - Query all data grouped by week for weekly view
  - Auto-switch between daily/weekly based on data age
- Add toggle or tab in widget to show/hide graph

**UI/UX Notes:**
- Graph should be collapsible/expandable to save space
- Show current value vs. first recorded value (gain/loss %)
- Color code: green for gains, red for losses
- Tooltip on hover showing exact date and value

**Dependencies:**
- Requires "Database Caching" enhancement to be implemented first
- Need to install chart library (Chart.js or Recharts)

**Related Files:**
- `backend/app/api/v1/endpoints/stocks.py`
- `backend/app/api/v1/endpoints/crypto.py`
- `backend/app/models/` (portfolio_history model)
- `frontend/src/components/widgets/StockTickerWidget.jsx`
- `frontend/src/components/widgets/CryptoWidget.jsx`

---

## Server Monitor

### Enhancements

#### Track Specific Processes
**Status:** Not Started
**Priority:** Medium
**Description:**
Add ability to monitor specific processes/services and their status.

**Requirements:**
- Configure list of processes to monitor per server (e.g., mysql, plex, game servers, nginx, docker)
- Display process status:
  - Running ✓ / Stopped ✗
  - CPU usage
  - Memory usage
  - Uptime
  - PID
- Alert/highlight when a monitored process is not running
- Allow user to configure process list in server settings

**Technical Implementation:**
- Agent side (Python):
  - Add `get_process_status(process_names)` function
  - Use `psutil.process_iter()` to find processes by name
  - Collect CPU, memory, uptime for each monitored process
  - Return status for each configured process
- Backend:
  - Update agent data model to include process_list
  - Store monitored process names in server configuration
- Frontend:
  - Add "Processes" section to server monitor widget
  - Show list of monitored processes with status indicators
  - Add setting to configure which processes to monitor

**Related Files:**
- `agent/monitor_agent.py`
- `backend/app/api/v1/endpoints/servers.py`
- `backend/app/models/server.py`
- `frontend/src/components/widgets/ServerMonitorWidget.jsx`

---

## Weather Widget

### Future Enhancements
- Severe weather alerts overlay on radar
- Golden hour times for photographers
- Moon phase display
- Air quality index
- Extended forecast (10-14 days)

---

## News Headlines Widget

### Enhancements

#### Priority Keywords with Highlighting
**Status:** Not Started
**Priority:** Medium
**Description:**
Add ability to define priority keywords that bump matching articles to the top of the list and highlight them for visibility.

**Requirements:**
- User-configurable list of priority keywords (e.g., "AI", "security breach", "local", "urgent")
- Articles matching priority keywords:
  - Move to top of the news list
  - Highlight with distinct visual style (e.g., yellow background, bold border, icon)
  - Show which keyword(s) matched
- Multiple keyword matches = higher priority (sort by match count)
- Case-insensitive keyword matching
- Match in title, description, or content

**Technical Implementation:**
- Backend:
  - Add `priority_keywords` field to news widget configuration
  - Score articles based on keyword matches
  - Sort articles by priority score (descending) before returning
  - Include matched keywords in response
- Frontend:
  - Add setting to configure priority keywords (comma-separated input)
  - Apply highlight styling to priority articles:
    - Background color (subtle yellow or blue)
    - Left border accent
    - Badge showing matched keywords
  - Display priority articles first in the list

**UI/UX Example:**
```
┌─────────────────────────────────────┐
│ 🔔 AI regulation bill passes        │ ← Yellow highlight
│    Keywords: AI, regulation         │
├─────────────────────────────────────┤
│ Security breach at major corp       │ ← Yellow highlight
│    Keywords: security breach        │
├─────────────────────────────────────┤
│ Regular news article...             │ ← Normal styling
│ Another regular article...          │
└─────────────────────────────────────┘
```

**Related Files:**
- `backend/app/api/v1/endpoints/news.py`
- `frontend/src/components/widgets/NewsWidget.jsx`
- `frontend/src/components/widgets/widgetRegistry.js` (add priority_keywords to config schema)

---

## Network Status Widget

### Enhancements (Phase 2)

#### Packet Loss Tracking & Latency Graphs
**Status:** Not Started
**Priority:** High
**Description:**
Enhance the existing Network Status Widget (Phase 1 - ping targets) with packet loss tracking, latency graphs, and uptime monitoring.

**Phase 1 Completed:**
- ✓ Custom ping targets configuration
- ✓ Multi-site ping tests
- ✓ Real-time latency display

**Phase 2 Requirements:**
- **Packet Loss Tracking:**
  - Calculate packet loss percentage per target
  - Display packet loss % next to each ping target
  - Highlight targets with packet loss > 5% in orange/red
  - Track consecutive failed pings

- **Latency Graphs:**
  - Historical latency graph per target (last 24 hours)
  - Mini sparkline graphs inline with each target
  - Expandable detailed graph showing latency trends
  - Color-coded zones (green: <50ms, yellow: 50-150ms, red: >150ms)
  - Show min/max/avg latency stats

- **Uptime Tracking:**
  - Track uptime percentage (last 24h, 7d, 30d)
  - Display uptime % in widget header
  - Show downtime incidents timeline
  - Calculate "nines" of availability (99.9%, 99.99%, etc.)
  - Alert when uptime drops below threshold

- **Enhanced Status Indicators:**
  - Connection quality indicator (Excellent/Good/Fair/Poor)
  - Visual status history bar showing last 24h (green/red segments)
  - "Last outage" timestamp
  - Total downtime duration

**Technical Implementation:**
- Backend:
  - Store ping results in database: `ping_history` table
    - Fields: timestamp, target, latency_ms, success, widget_id
  - Endpoint to query historical data with time ranges
  - Calculate packet loss and uptime metrics on backend
  - Add background job to clean up old ping data (keep 30 days)

- Frontend:
  - Add Chart.js or Recharts for latency graphs
  - Implement sparkline component for inline graphs
  - Add expandable graph section per target
  - Display packet loss % with color coding
  - Show uptime stats prominently
  - Add time range selector (24h/7d/30d)

**Benefits:**
- Identify intermittent connection issues
- Track ISP reliability over time
- Visual proof of network problems
- Proactive alerting before total outages

**Related Files:**
- `backend/app/api/v1/endpoints/network.py`
- `backend/app/models/network.py` (new)
- `frontend/src/components/widgets/NetworkStatusWidget.jsx`
- Database migration for ping_history table

---

## Network Speed & Connection Status Widget

### New Widget

#### Internet Speed Test & Connection Monitor
**Status:** Not Started
**Priority:** Medium
**Description:**
Widget to monitor internet connection status and run network speed tests.

**Requirements:**
- **Connection Status:**
  - Show online/offline status with indicator
  - Display current ISP/network name
  - Show connection type (WiFi, Ethernet, etc.)
  - Latency/ping to common servers

- **Speed Test:**
  - On-demand speed test button
  - Show download speed (Mbps)
  - Show upload speed (Mbps)
  - Show ping/latency (ms)
  - Show jitter
  - Progress indicator during test

- **Historical Tracking:**
  - Graph of speed test results over time
  - Track daily average speeds
  - Highlight speed drops or connection issues
  - Show best/worst speeds recorded

- **Alerts:**
  - Notify when connection drops
  - Alert if speeds are below configured threshold
  - Track uptime percentage

**Technical Implementation:**
- Backend:
  - Speed test endpoint using speedtest-cli or Ookla API
  - Store test results in database with timestamps
  - Connection monitoring endpoint (ping check)
  - Table: `speedtest_history` (user_id, timestamp, download_speed, upload_speed, ping, jitter, server)

- Frontend:
  - Speed test controls (run test button)
  - Real-time progress display during test
  - Chart showing historical speeds (Chart.js or Recharts)
  - Connection status indicator with last check time
  - Configurable alert thresholds in settings

**Use Cases:**
- Monitor home internet performance
- Track ISP reliability
- Identify network issues
- Verify ISP is delivering promised speeds
- Historical performance tracking

**Alternatives:**
- Option 1: Use speedtest-cli Python package (free, accurate)
- Option 2: Use Ookla Speedtest API (official but may have limits)
- Option 3: Use custom ping/download tests (less accurate)

**Related Files:**
- `backend/app/api/v1/endpoints/network.py` (new)
- `backend/app/models/speedtest.py` (new)
- `frontend/src/components/widgets/NetworkWidget.jsx` (new)
- `frontend/src/components/widgets/widgetRegistry.js`

---

## General / Other Widgets

_(Add more items here as needed)_

---

## Completed Items

### Stock & Crypto Database Caching ✓
**Completed:** 2026-02-10
**Description:**
Implemented historical price storage to prevent blank widgets when API rate limits are hit. Data is cached in database and used as fallback when external APIs fail.

**Implemented Features:**
- Database tables for historical data:
  - `stock_quotes` - All stock price data points
  - `crypto_prices` - All crypto price data points
- API endpoints store successful fetches with 15-minute deduplication
- Database fallback when API calls fail (prevents blank widgets)
- Widget refresh intervals increased to 20 minutes
- ~92% reduction in API calls per user
- Historical data accumulates naturally for future graphing
- "Last updated" timestamp indicators on widgets

**Technical Implementation:**
- Backend:
  - New models: `StockQuote`, `CryptoPrice`
  - CRUD operations in `app/crud/finance.py`
  - Store-and-fallback pattern in finance endpoints
  - 15-minute deduplication to prevent excessive storage
- Frontend:
  - 20-minute minimum refresh intervals (was 60 seconds)
  - "Last updated" time display with formatTimeAgo()
  - Updated widget registry defaults
- Storage: ~3-4 records/hour/symbol (~19 MB/year for typical usage)

**Benefits:**
- No more blank widgets when APIs fail
- Resilient to API rate limits and outages
- Reduced API calls (better for free tier limits)
- Historical data ready for portfolio value graphs

**Files Modified:**
- `backend/app/models/finance.py` - New models
- `backend/app/crud/finance.py` - New CRUD operations
- `backend/alembic/versions/29a342be5504_add_stock_crypto_prices.py` - Migration
- `backend/app/models/__init__.py` - Export new models
- `backend/app/api/v1/endpoints/finance.py` - Fallback logic + deduplication
- `frontend/src/components/widgets/StockTickerWidget.jsx` - 20-min intervals
- `frontend/src/components/widgets/CryptoWidget.jsx` - 20-min intervals
- `frontend/src/components/widgets/widgetRegistry.js` - Updated defaults

### Server Monitor - Monitor Mounted Drives Status ✓
**Completed:** 2026-02-10
**Description:**
Added drive/mount monitoring to Server Monitor widget with usage tracking and status indicators.

**Implemented Features:**
- User-configurable mount points per server
- Drive usage stats (used/total/percentage)
- Support for both actual mount points and directories
- Visual indicators:
  - Color-coded usage bars (green/yellow/red)
  - Warning icon (⚠️) for unmounted drives
  - Lock icon (🔒) for read-only mounts
  - Emoji icons based on filesystem type (💾🏠📁🌐)
- Add/delete drives via UI
- Agent collection with psutil
- Graceful handling of inaccessible paths

**Files Modified:**
- `agent/dash_agent.py` - Drive collection logic
- `backend/app/models/server.py` - MonitoredDrive model
- `backend/app/schemas/server.py` - Drive schemas
- `backend/app/crud/server.py` - CRUD operations
- `backend/app/api/v1/endpoints/servers.py` - API endpoints
- `backend/alembic/versions/*_add_monitored_drives.py` - Migration
- `frontend/src/components/widgets/ServerMonitorWidget.jsx` - UI components
- `frontend/src/components/widgets/widgetRegistry.js` - Settings
