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

#### Improve Delivery Removal Timing
**Status:** Not Started
**Priority:** Medium
**Estimated Effort:** ~2-3 hours
**Description:**
Currently, packages are removed exactly 24 hours after delivery confirmation. This should be changed to remove packages at midnight the following day, giving users the full day to see the delivery notification.

**Current Behavior:**
- Package delivered at 2:00 PM on Monday
- Removed at 2:00 PM on Tuesday (24 hours later)
- ❌ User might miss the delivery if they only check in the morning

**Desired Behavior:**
- Package delivered at 2:00 PM on Monday
- Highlighted/marked as delivered immediately (green background, checkmark)
- Remains visible for the rest of Monday
- Removed at midnight (12:00 AM) on Wednesday morning
- ✅ User has all of Tuesday to see it was delivered

**Technical Implementation:**
- Update cleanup task in `scheduler.py`
- Instead of: `delivered_at <= now - 24 hours`
- Use: `delivered_at < start_of_today` (where start_of_today is midnight)
- This gives users the full next day to see the delivery

**Example Logic:**
```python
from datetime import datetime, time

# Current time: Tuesday 10:00 AM
now = datetime.now()
start_of_today = datetime.combine(now.date(), time.min)  # Tuesday 12:00 AM

# Remove packages delivered before start of today
# Packages delivered Monday (any time) → Removed Wednesday 12:00 AM
# Packages delivered Sunday → Removed Tuesday 12:00 AM
cutoff_time = start_of_today
```

**Benefits:**
- User sees delivery for the entire following day
- More predictable removal time (always midnight)
- Better UX - no missed notifications
- Still automatic cleanup (no manual deletion needed)

**Related Files:**
- `backend/app/core/scheduler.py` - Update `cleanup_delivered_packages_task()`
- Current cutoff: `datetime.now() - timedelta(hours=24)`
- New cutoff: `datetime.combine(datetime.now().date(), time.min)`

---

### Completed

#### Auto-remove Delivered Packages ✓
**Completed:** 2026-02-12
**Description:**
Implemented automatic detection of delivery confirmations and removal of delivered packages.

**Implemented Features:**
- ✅ Delivery confirmation detection from emails
- ✅ Email metadata tracking (source, subject, sender, body)
- ✅ Tracking URL extraction from emails
- ✅ Spam prefix cleaning
- ✅ Auto-removal after 24 hours (to be improved - see above)
- ✅ Green highlighting for delivered packages
- ✅ Background cleanup task (runs every 6 hours)

**Files Modified:**
- `backend/app/api/v1/endpoints/email_scanner.py`
- `backend/app/api/v1/endpoints/email_credentials.py`
- `backend/app/core/scheduler.py`
- `backend/app/crud/package.py`
- `backend/app/models/package.py`

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

### Enhancements

#### Moon Phase Tracker with Sunrise Countdown
**Status:** Not Started
**Priority:** Low-Medium
**Estimated Effort:** ~4-6 hours
**Description:**
Add a moon phase visualization that shows the current moon phase and tracks time until sunrise, similar to the existing sun progression bar.

**Requirements:**
- Display current moon phase with appropriate emoji/icon:
  - 🌑 New Moon
  - 🌒 Waxing Crescent
  - 🌓 First Quarter
  - 🌔 Waxing Gibbous
  - 🌕 Full Moon
  - 🌖 Waning Gibbous
  - 🌗 Last Quarter
  - 🌘 Waning Crescent
- Show progression bar from current time to next sunrise
- Animated moon icon that moves along the bar (like the sun indicator)
- Display time until sunrise (e.g., "5h 23m until sunrise")
- Moon illumination percentage (e.g., "87% illuminated")
- Place below or adjacent to sun progression bar

**Technical Implementation:**
- Backend: Add moon phase calculation endpoint
  - Use astronomy library (e.g., `ephem`, `skyfield`, or `astral`)
  - Calculate moon phase based on date/time
  - Calculate illumination percentage
  - Return moon phase name, percentage, and emoji
- Frontend: Create MoonProgressBar component
  - Similar structure to sun progression bar
  - Calculate progress from midnight to sunrise
  - Animate moon icon position
  - Display moon phase emoji and stats
- API: Free astronomical APIs available (e.g., Open-Meteo astronomy endpoint)

**UI/UX Notes:**
- Keep visual style consistent with sun progression bar
- Use subtle gradient (dark blue/purple for night)
- Moon icon should be clearly visible against background
- Show countdown timer that updates in real-time

**Related Files:**
- `backend/app/api/v1/endpoints/weather.py`
- `frontend/src/components/widgets/WeatherWidget.jsx`

---

### Future Enhancements
- Severe weather alerts overlay on radar
- Golden hour times for photographers
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

## Calendar Widget

### Enhancements

#### Smart Event Display with Progressive Fallback
**Status:** Not Started
**Priority:** Medium
**Estimated Effort:** ~3-4 hours
**Description:**
Implement intelligent event display logic that adapts based on what events are available, preventing empty calendar displays.

**Requirements:**
- **Display Priority Logic:**
  1. **If events exist today:** Show today's events (default behavior)
  2. **If no events today:** Automatically show this week's events
  3. **If no events this week:** Automatically show this month's events
  4. **If no events this month:** Show "No upcoming events" message

- **Visual Indicators:**
  - Display current view mode: "Today", "This Week", or "This Month"
  - Show date range being displayed (e.g., "Feb 12 - Feb 18")
  - Highlight which fallback level is active
  - Option to manually toggle between views

- **Event Display:**
  - Today view: Show all events for current day with times
  - Week view: Group events by day, show 7 days starting from today
  - Month view: Calendar grid or list view of upcoming events

**Technical Implementation:**
- Backend: Update calendar endpoint with query parameters
  - Add `view` parameter: "today", "week", "month"
  - Add `auto_fallback` parameter (default: true)
  - Return events + metadata about which view was used
  - Include event counts per view (e.g., "0 today, 3 this week")
- Frontend: Implement fallback logic
  - Fetch event counts for today/week/month
  - Automatically select appropriate view based on data
  - Display view selector/indicator
  - Cache view preference per user
- Google Calendar API: Query optimization
  - Single API call to fetch month's events
  - Frontend filters for today/week views
  - Reduces API calls and improves performance

**UI/UX Notes:**
- Smooth transitions between view modes
- Clear indication of which view is active
- "No events" state should suggest adding events
- Option to force specific view (user override)
- Week view shows Mon-Sun or configurable start day

**Benefits:**
- Never shows empty calendar
- User always sees relevant upcoming events
- Reduces need for manual navigation
- Better use of widget space
- More informative at a glance

**Related Files:**
- `backend/app/api/v1/endpoints/calendar.py` (or create if doesn't exist)
- `frontend/src/components/widgets/CalendarWidget.jsx` (or create if doesn't exist)
- Google Calendar API integration

**Dependencies:**
- Calendar widget must be implemented first (if not already)
- Google Calendar API integration
- Authentication with Google OAuth

---

## Dashboard Core / Infrastructure

### Enhancements

#### Widget Alert System - Priority Movement to Top
**Status:** Not Started
**Priority:** High
**Estimated Effort:** ~8-12 hours
**Description:**
Build a framework that allows any widget to temporarily move to the top of the dashboard when it has an important message or alert. Once the user views or acknowledges the alert, the widget returns to its original position.

**Phase 1: Core Infrastructure** (This enhancement)
Build the basic mechanism for widgets to alert and move to top. Per-widget trigger conditions will be added in Phase 2.

**Requirements:**

- **Alert State Management:**
  - Widgets can enter "alert mode" via API call
  - Backend tracks which widgets are currently alerting
  - Store original widget position before moving
  - Persist alert state across page refreshes

- **Layout Management:**
  - Automatically move alerted widget to top-left position (0, 0)
  - Shift other widgets down to make space
  - Smooth animation during position changes
  - Support multiple simultaneous alerts (stack at top by priority)

- **Visual Indicators:**
  - Alerted widgets have distinct styling:
    - Pulsing border (red/orange/yellow based on severity)
    - Background highlight
    - Alert icon/badge in corner
    - Optional: Subtle shake animation on alert
  - Non-alerted widgets slightly dimmed when alerts active
  - Clear "Acknowledge" or "Dismiss" button on alerted widget

- **Acknowledgment Flow:**
  1. User clicks "Acknowledge" or interacts with alert
  2. Widget returns to original position
  3. Layout animates back to normal
  4. Alert state cleared from backend
  5. Visual styling returns to normal

- **Alert Severity Levels:**
  - **Critical** (red): Security alerts, system failures
  - **Warning** (orange): Important notifications, thresholds exceeded
  - **Info** (blue): General notifications, updates available

**Technical Implementation:**

**Backend:**
- Database schema changes:
  ```sql
  ALTER TABLE widget_configs ADD COLUMN alert_active BOOLEAN DEFAULT FALSE;
  ALTER TABLE widget_configs ADD COLUMN alert_severity VARCHAR(20);
  ALTER TABLE widget_configs ADD COLUMN alert_message TEXT;
  ALTER TABLE widget_configs ADD COLUMN alert_triggered_at DATETIME;
  ALTER TABLE widget_configs ADD COLUMN original_layout_x INT;
  ALTER TABLE widget_configs ADD COLUMN original_layout_y INT;
  ```

- New endpoint: `POST /api/v1/widgets/{widget_id}/alert`
  ```json
  {
    "severity": "warning",
    "message": "Server disk usage at 95%",
    "auto_dismiss_seconds": 300  // Optional
  }
  ```

- New endpoint: `POST /api/v1/widgets/{widget_id}/acknowledge`
  - Clears alert state
  - Returns original position
  - Logs acknowledgment

- Middleware to inject alert status into widget data responses

**Frontend:**

- Dashboard state management:
  - Track alerted widgets
  - Store original layouts
  - Manage layout transitions

- React Grid Layout modifications:
  - Detect when widget enters alert mode
  - Calculate new layout with alerted widgets at top
  - Animate position changes using react-grid-layout's `onLayoutChange`

- Alert UI components:
  - `<AlertBadge>` - Shows severity icon
  - `<AlertBanner>` - Message bar within widget
  - `<AcknowledgeButton>` - Dismissal control

- Styling (Tailwind):
  ```jsx
  // Critical alert
  className="ring-4 ring-red-500 ring-opacity-50 animate-pulse"

  // Warning alert
  className="ring-4 ring-orange-500 ring-opacity-50"

  // Info alert
  className="ring-4 ring-blue-500 ring-opacity-50"
  ```

**UI/UX Design:**

```
┌──────────────────────────────────────────┐
│ ⚠️ Server Monitor Widget (ALERT)         │ ← Pulsing red border
│ ┌────────────────────────────────────┐   │
│ │ 🔴 WARNING: Disk usage at 95%      │   │ ← Alert banner
│ │ Server: web-01 (/dev/sda1)         │   │
│ │                                     │   │
│ │ [View Details] [Acknowledge]       │   │ ← Action buttons
│ └────────────────────────────────────┘   │
│ (normal widget content below...)          │
└──────────────────────────────────────────┘
```

**Position Management Logic:**
```javascript
// When alert triggered:
1. Save current position: originalLayout[widgetId] = {x, y, w, h}
2. Move widget to top: {x: 0, y: 0, w: widget.w, h: widget.h}
3. Shift other widgets down by widget.h rows
4. Apply alert styling

// When acknowledged:
1. Restore original position from originalLayout[widgetId]
2. Shift other widgets back up
3. Remove alert styling
4. Clear originalLayout[widgetId]
```

**Alert Priority System (for multiple alerts):**
- Critical alerts always at top
- Stack alerts by severity then timestamp
- Layout: [Critical1] [Critical2] [Warning1] [Info1] [Normal Widgets...]

**Configuration Options (per widget):**
- Enable/disable alert capability
- Auto-dismiss timeout (optional)
- Custom alert messages/templates
- Severity level overrides

**Benefits:**
- ✅ Immediate visibility for critical issues
- ✅ Works with any widget type
- ✅ Non-intrusive (user can acknowledge)
- ✅ Maintains dashboard organization
- ✅ Clear visual hierarchy

**Future Enhancements (Phase 2):**
- Per-widget trigger conditions:
  - Server Monitor: CPU > 90%, Disk > 95%, Process down
  - Package Tracker: Package out for delivery
  - Weather: Severe weather alert
  - Stock: Price drops > X%
  - News: Priority keyword detected
- Alert history/log viewer
- Sound notifications (optional)
- Browser notifications integration
- Alert scheduling (quiet hours)
- Email/SMS integration for critical alerts

**Related Files:**
- `backend/app/models/widget.py` - Add alert fields
- `backend/app/api/v1/endpoints/widgets.py` - Alert endpoints
- `frontend/src/components/Dashboard.jsx` - Layout management
- `frontend/src/hooks/useAlertSystem.js` - Alert state management
- `frontend/src/components/AlertBadge.jsx` - Alert UI components

**Dependencies:**
- None (pure addition to existing widget system)

**Testing Scenarios:**
1. Single widget alerts and returns to position
2. Multiple widgets alert simultaneously (stacking)
3. User acknowledges alerts in different order
4. Page refresh with active alerts (state persistence)
5. Alert triggered while user is editing layout
6. Widget deleted while in alert mode

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
