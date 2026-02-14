# Personal Dash - Backlog (Bugs & Enhancements)

> **Note:** This file tracks bugs and enhancement ideas for future work.

---

## Priority Summary

### High Priority (Do Next)
1. **Custom Widget System** (~15-20 hours) - Generic database-driven widgets ← **NEXT**
   - See `docs/CUSTOM_WIDGET_SPEC.md` for complete specification
   - Users populate database tables, dashboard renders automatically
   - Supports display, links, visibility, alerts, acknowledgment

### Medium Priority (Soon)
3. **News: Priority Keywords** - Already partially implemented, needs UI enhancement
4. **Server Monitor: Track Specific Processes** - Already completed, but may need additional features
5. **Smart Home Widget** (~10-15 hours) - Home Assistant integration

### Lower Priority (Later)
6. **Network Status Widget Phase 2** - Packet loss and uptime tracking (Phase 1 & 3 completed)
7. **Deployment & Documentation** (~10-20+ hours) - Production deployment guide

### Deferred (External Dependencies / Scope TBD)
8. **Fitness Stats Widget** - Deferred pending decision on Garmin Connect integration scope
9. **Picture Frame Widget** - Deferred due to external project dependency

---

## Package Tracker

### Enhancements

#### Improve Delivery Removal Timing ✓
**Status:** ✅ **COMPLETED** (2026-02-12)
**Priority:** Medium
**Estimated Effort:** ~2-3 hours
**Description:**
~~Currently, packages are removed exactly 24 hours after delivery confirmation.~~ Changed to remove packages at midnight the following day, giving users the full day to see the delivery notification.

**Previous Behavior:**
- Package delivered at 2:00 PM on Monday
- Removed at 2:00 PM on Tuesday (24 hours later)
- ❌ User might miss the delivery if they only check in the morning

**New Behavior:**
- Package delivered at 2:00 PM on Monday
- Highlighted/marked as delivered immediately (green background, checkmark)
- Remains visible for the rest of Monday
- Removed at midnight (12:00 AM) on Tuesday
- ✅ User has the rest of Monday to see it was delivered

**Implementation:**
```python
# Calculate midnight of the day after delivery
delivered_date = package.delivered_at.date()
next_midnight = datetime.combine(
    delivered_date + timedelta(days=1),
    datetime.min.time()
)

# Remove if we're past that midnight
if now >= next_midnight:
    package.dismissed = True
```

**Benefits:**
- ✅ User sees delivery for the rest of delivery day
- ✅ More predictable removal time (always midnight)
- ✅ Better UX - no missed notifications
- ✅ Still automatic cleanup (no manual deletion needed)

**Files Modified:**
- `backend/app/core/scheduler.py` - Updated `cleanup_delivered_packages_task()`
  - Changed from: `cutoff_time = now - timedelta(hours=24)`
  - Changed to: Calculate next midnight for each package individually

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

### Completed

#### Portfolio Value Graph ✓
**Completed:** 2026-02-13
**Description:**
Added portfolio value graphs to Stock and Crypto widgets showing total portfolio value over time.

**Implemented Features:**
- ✅ Historical portfolio value calculation using existing price data
- ✅ Two new API endpoints:
  - `GET /api/v1/finance/stocks/portfolio-history`
  - `GET /api/v1/finance/crypto/portfolio-history`
- ✅ Reusable PortfolioGraph component (Recharts-based)
- ✅ Display modes:
  - Daily data points for ≤30 days
  - Weekly aggregation for >30 days
- ✅ Summary statistics:
  - Current portfolio value
  - Starting value
  - Total gain/loss percentage
- ✅ Visual features:
  - Color-coded line (green for gains, red for losses)
  - Formatted currency display
  - Tooltips with date and value
  - Responsive container (200px height)
- ✅ Expandable section (collapsed by default)
- ✅ Lazy loading (only fetches when expanded)
- ✅ Manual refresh button
- ✅ Error handling and loading states

**Portfolio vs Watchlist Enhancement:**
- ✅ Added holding type field: "portfolio" or "watchlist"
- ✅ Portfolio holdings (💼) - owned stocks/crypto, included in calculations
- ✅ Watchlist items (👁️) - price tracking only, excluded from calculations
- ✅ Type selection in Add modal
- ✅ Visual indicators per holding
- ✅ Automatic migration of existing holdings to "portfolio" type
- ✅ Separate counts displayed in header

**Technical Implementation:**
- Backend:
  - New schemas: `PortfolioDataPoint`, `PortfolioHistoryResponse`
  - CRUD function: `calculate_portfolio_history()` in `app/crud/finance.py`
  - Uses existing `stock_quotes` and `crypto_prices` tables
  - Forward-fill logic for missing data
  - Percentage change calculations from starting value
- Frontend:
  - Component: `PortfolioGraph.jsx`
  - Integrated into `StockTickerWidget.jsx`
  - Integrated into `CryptoWidget.jsx`
  - Uses Recharts library (already installed)
  - Follows WeatherWidget expandable pattern

**Known Issues:**
- Graph may show "no change" if holdings have different data collection start times
- Only calculates portfolio value for dates where ALL holdings have price data
- Debug logging available for troubleshooting

**Files Modified:**
- `backend/app/schemas/finance.py` - NEW
- `backend/app/crud/finance.py` - Added portfolio calculation
- `backend/app/api/v1/endpoints/finance.py` - Added 2 endpoints
- `frontend/src/components/widgets/PortfolioGraph.jsx` - NEW
- `frontend/src/components/widgets/StockTickerWidget.jsx` - Graph integration + type field
- `frontend/src/components/widgets/CryptoWidget.jsx` - Graph integration + type field

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

### Completed

#### Moon Phase Tracker with Smart Day/Night Progression Bar ✓
**Completed:** 2026-02-14
**Priority:** High
**Actual Effort:** ~2 hours
**Description:**
Implemented moon phase visualization with smart day/night progression bar that automatically switches between sun and moon modes.

**Implemented Features:**

**Part 1: Moon Phase Display** ✅
- Current moon phase emoji (🌑🌒🌓🌔🌕🌖🌗🌘)
- Moon phase name (e.g., "Waxing Gibbous")
- Illumination percentage (0-100%)
- Placed between sun times and hourly forecast

**Part 2: Smart Day/Night Progression Bar** ✅
- **DAY MODE (sunrise to sunset):**
  - Sun ☀️ indicator progressing from sunrise → sunset
  - Orange/yellow gradient (warm colors)
  - Shows "Xh Ym until sunset"

- **NIGHT MODE (sunset to sunrise):**
  - Moon 🌙 indicator progressing from sunset → next sunrise
  - Indigo/purple gradient (night sky colors)
  - Shows "Xh Ym until sunrise"
  - Handles midnight correctly (progress continues through midnight)

**Technical Implementation:**
- Backend:
  - `calculate_moon_phase()` function using astronomical formula
  - Reference: January 6, 2000 new moon
  - Lunar synodic month: 29.530588853 days
  - No external dependencies (pure math)
  - Added `MoonPhase` model to API response
  - Fixed cross-platform time formatting (%-I → %I with lstrip)

- Frontend:
  - `MoonPhase` component for phase display
  - Enhanced `SunTimes` component to smart day/night bar
  - Automatic mode detection based on current time
  - `formatTimeRemaining()` helper function
  - Smooth animated transitions

**Files Modified:**
- `backend/app/api/v1/endpoints/weather.py`
- `frontend/src/components/widgets/WeatherWidget.jsx`

**Documentation:**
- `MOON_PHASE_IMPLEMENTATION.md` - Complete implementation guide

---

#### Severe Weather Alerts ✓
**Completed:** 2026-02-14
**Priority:** High
**Actual Effort:** ~6 hours
**Description:**
Integrated National Weather Service API for real-time severe weather alerts with visual overlay on radar map and automatic widget alert triggering.

**Implemented Features:**

**Alert Display:**
- ✅ NWS API integration (free, no key, US only)
- ✅ Color-coded alert polygons on radar map:
  - 🔴 Extreme (red) - Tornadoes, extreme weather
  - 🟠 Severe (orange) - Severe thunderstorms, flash floods
  - 🟡 Moderate (yellow) - Watches, advisories
  - 🔵 Minor (blue) - Minor advisories
- ✅ Clickable polygons with popup details
- ✅ Alert list display (event, headline, expiration)
- ✅ Toggle button to show/hide alerts on map
- ✅ Alert count indicator

**Widget Alert System Integration:**
- ✅ Background monitoring task (every 5 minutes)
- ✅ Auto-triggers widget alerts for urgent weather (Immediate/Expected urgency)
- ✅ Severity mapping: NWS Extreme → Critical, Severe → Warning
- ✅ Auto-clears widget alerts when weather threat ends
- ✅ Alert aggregation (shows multiple alerts)

**Technical Implementation:**
- Backend:
  - `fetch_nws_alerts(lat, lon)` - GeoJSON polygon support
  - `GET /weather/alerts` endpoint
  - `WeatherAlert` and `WeatherAlertsResponse` schemas
  - `monitor_weather_alerts_task()` scheduler job
  - Alert severity to widget severity mapping
- Frontend:
  - `AlertsOverlay` component (Leaflet GeoJSON layers)
  - `WeatherAlertsList` component
  - Independent 5-minute alert refresh
  - Alert toggle button

**Files Modified:**
- `backend/app/api/v1/endpoints/weather.py` - NWS integration
- `backend/app/core/scheduler.py` - Monitoring task
- `frontend/src/components/widgets/WeatherWidget.jsx` - Alert display

**Documentation:**
- `SEVERE_WEATHER_ALERTS_IMPLEMENTATION.md` - Complete guide

---

### Future Enhancements
- International weather alerts (Canada: Environment Canada, Europe: MeteoAlarm)
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

### Completed

#### Smart Event Display with Progressive Fallback ✓
**Completed:** 2026-02-13
**Priority:** Medium
**Actual Effort:** ~3 hours
**Description:**
Implemented intelligent event display logic that adapts based on what events are available, preventing empty calendar displays.

**Implemented Features:**
- ✅ **Progressive Fallback Logic:**
  - Auto-selects "Today" if events exist today
  - Falls back to "Week" if no events today but events this week
  - Falls back to "Month" if no events this week but events this month
  - Shows "Today" with empty state if no events at all

- ✅ **Visual Indicators:**
  - Event counts displayed below each tab (Today/Week/Month)
  - Smart View indicator shows auto-selected view and reason
  - Blue info box: "Smart View: Showing This Week (5 events)"
  - Clear visual feedback on which view is active

- ✅ **Manual Override Support:**
  - User can click any tab to override auto-selection
  - Manual selection persists until month navigation
  - Smart View indicator disappears when manually overridden

- ✅ **Performance Optimizations:**
  - Single API call per load (fetches month, filters client-side)
  - 10-minute cache for fast reloads
  - Instant view switching (no re-fetch)
  - O(n) event counting where n < 100 typically

**Technical Implementation:**
- Backend (`calendar.py`):
  - Added `auto_fallback` query parameter (default: true)
  - Added event count metadata: `events_today_count`, `events_week_count`, `events_month_count`
  - Added `auto_selected_view` field to response
  - Helper functions: `calculate_date_ranges()`, `select_best_view()`, `count_events_in_range()`
  - Fixed date range filtering bug (use `<` instead of `<=` for end boundary)

- Frontend (`CalendarWidget.jsx`):
  - Added `userOverrodeView` state tracking
  - Updated ViewTabs to show event counts
  - Auto-sync view with backend's selection
  - Smart View indicator component
  - Reset auto-fallback on month navigation

**Bugs Fixed:**
- ✅ Date range filtering now correctly excludes end boundary
- ✅ Events on Feb 14 no longer appear in Feb 13's "today" view
- ✅ Timezone handling uses local server time (not UTC)

**Files Modified:**
- `backend/app/api/v1/endpoints/calendar.py`
- `frontend/src/components/widgets/CalendarWidget.jsx`

**Documentation:**
- `CALENDAR_SMART_VIEW_IMPLEMENTATION.md` - Complete implementation guide
- `test_calendar_logic.py` - Unit tests for date logic
- `test_calendar_smart_view.py` - Integration tests

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

#### Smart Widget Refresh - Only Update Changed Data
**Status:** Not Started
**Priority:** Medium
**Estimated Effort:** ~6-8 hours
**Description:**
Optimize widget refresh behavior to only re-render widgets when their data has actually changed, reducing screen flashing and blanking during background refreshes.

**Current Behavior:**
- Dashboard polls all widgets on a fixed interval (60 seconds for alerts)
- All widgets refresh simultaneously even if data hasn't changed
- Causes visual flashing/blanking as widgets re-render
- Unnecessary re-renders impact performance and UX

**Desired Behavior:**
- Backend includes data hash or timestamp in API responses
- Frontend compares new data with previous data
- Only re-render widget if data has actually changed
- Skip re-render if data is identical to previous fetch
- Smooth, flash-free experience when data is static

**Technical Implementation:**

**Backend:**
- Add `data_hash` or `last_modified` field to API responses
- Calculate hash of response data (MD5/SHA1 of JSON)
- OR: Use timestamp of when underlying data last changed
- Include in response metadata:
  ```json
  {
    "data": { /* widget data */ },
    "meta": {
      "hash": "abc123...",
      "last_updated": "2026-02-13T12:34:56Z"
    }
  }
  ```

**Frontend:**
- Store previous data hash per widget in `useWidgetData` hook
- Compare new hash with previous on each fetch
- Only update state if hash differs:
  ```javascript
  if (newHash !== previousHash) {
    setData(newData);  // Trigger re-render
  } else {
    // Skip update, no re-render
  }
  ```
- Update loading states intelligently:
  - First load: Show loading spinner
  - Background refresh: Silent (no loading state)
  - Data changed: Update without flash

**Alternative Implementation:**
- Deep equality check instead of hash
  ```javascript
  import isEqual from 'lodash/isEqual';
  if (!isEqual(newData, prevData)) {
    setData(newData);
  }
  ```
- Pro: No backend changes needed
- Con: Performance cost of deep comparison (acceptable for small datasets)

**Optimization Options:**
1. **Per-widget hashing:** Each endpoint calculates its own hash
2. **Client-side comparison:** Frontend does deep equality check
3. **ETag headers:** Use HTTP ETag for cache validation (more complex)
4. **Timestamp comparison:** Track `updated_at` in database for each data source

**Benefits:**
- ✅ Eliminates unnecessary re-renders
- ✅ Reduces screen flashing/blanking
- ✅ Smoother user experience
- ✅ Better performance (fewer DOM updates)
- ✅ Lower CPU usage
- ✅ More responsive dashboard

**Example Widgets That Benefit Most:**
- **Weather:** Data updates every 15 min, polled every 60s
- **Stocks/Crypto:** Prices cached 20 min, polled every 60s
- **Server Monitor:** Metrics change slowly
- **Calendar:** Events rarely change during the day
- **News:** Headlines update hourly

**Edge Cases to Handle:**
- Widget settings changed (force refresh)
- Manual refresh button clicked (force refresh)
- Network errors (show error, don't blank widget)
- First load vs background refresh (different UX)

**Configuration:**
- Per-widget setting: `smart_refresh` (default: true)
- Global setting: `enable_smart_refresh` (default: true)
- Debug mode: Log when refreshes are skipped

**Related Files:**
- `frontend/src/hooks/useWidgetData.js` - Main refresh logic
- `frontend/src/hooks/useDashboard.js` - Dashboard-level polling
- `backend/app/api/v1/endpoints/*.py` - Add hash/timestamp to responses
- All widget components - Benefit from reduced re-renders

**Dependencies:**
- None (pure enhancement to existing system)

**Testing Scenarios:**
1. Data unchanged - verify no re-render
2. Data changed - verify smooth update
3. Network error - verify widget doesn't blank
4. Manual refresh - verify force update works
5. Settings changed - verify force update works
6. Multiple widgets - verify independent refresh logic

**Metrics to Track:**
- Number of skipped refreshes (should be high)
- Number of actual updates (should be low)
- Time saved from avoided re-renders
- User-reported reduction in flashing

---

## Deferred Widgets

### Fitness Stats Widget
**Status:** Deferred
**Priority:** Low (pending scope decision)
**Estimated Effort:** ~5-6 hours
**Description:**
Body weight tracking widget with historical charts. Deferred pending decision on whether Garmin Connect integration is in scope for this project.

**Potential Requirements:**
- Manual body weight entry
- Historical tracking with line chart
- Goal setting and progress tracking
- BMI calculation
- Weight trends (7-day/30-day averages)
- **Optional:** Garmin Connect integration for automatic sync

**Technical Implementation:**
- Backend:
  - `weight_entries` table (user_id, date, weight, notes)
  - API endpoints for CRUD operations
  - Optional: Garmin Connect API integration
- Frontend:
  - Weight entry form
  - Recharts line graph showing weight over time
  - Summary stats (current, goal, change)
  - Date range selector

**Decision Required:**
- Should this widget include Garmin Connect integration?
- Or keep it simple with manual entry only?

---

### Picture Frame Widget
**Status:** Deferred
**Priority:** Low (external dependency)
**Estimated Effort:** ~4-5 hours
**Description:**
Digital photo frame widget that displays images from a directory. Deferred due to external project dependency.

**Requirements:**
- Display images from configured directory path
- Display modes:
  - Slideshow (auto-advance with configurable interval)
  - Random (new random image on each load)
  - Sequential (cycle through images in order)
- Image controls:
  - Next/Previous buttons
  - Pause/Play for slideshow
  - Full-screen view option
- Settings:
  - Directory path configuration
  - Slideshow interval (5s, 10s, 30s, 1min)
  - Display mode selection
  - Image fit (cover/contain)

**Technical Implementation:**
- Backend:
  - Endpoint to list images from directory
  - Image serving endpoint (static file serving)
  - Support for common formats (jpg, png, gif, webp)
  - Error handling for missing/invalid paths
- Frontend:
  - Image carousel component
  - Auto-advance timer for slideshow
  - Responsive image display
  - Loading states for large images

**External Dependency:**
- Requires image source/collection to be set up first
- May need separate photo management system

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

---

## Custom Widget System

### Overview
**Status:** Design Complete - Ready to Implement
**Priority:** High (Next Major Feature)
**Estimated Effort:** ~15-20 hours
**Specification:** `docs/CUSTOM_WIDGET_SPEC.md`

**Description:**
A generic database-driven widget system that allows users to create custom dashboard widgets without writing code. Users populate database tables, and the dashboard automatically renders the data with full support for alerts, links, visibility control, and acknowledgment.

### Key Features

#### Core Capabilities
- ✅ Display custom data in list/table/grid formats
- ✅ External links (clickable items that open URLs)
- ✅ Conditional visibility (show/hide items via database flag)
- ✅ Alert triggering (automatic widget alerts based on data)
- ✅ Acknowledgment system (users can acknowledge alerts via UI)
- ✅ Styling options (icons, colors, highlights)
- ✅ Sorting and prioritization
- ✅ Multi-user isolation (per-user widgets and data)

#### Use Cases
1. **Service Health Monitoring** - Bash scripts check services, update database
2. **Sales KPI Dashboard** - Hourly scripts pull metrics from CRM/database
3. **Task/Reminder System** - Alert on overdue tasks, deadlines
4. **External Alert Aggregator** - Consolidate PagerDuty, Datadog, etc.
5. **Custom Status Boards** - Project status, team availability

### Database Schema

#### Table: `custom_widgets`
Widget configuration (one per widget instance):
```sql
CREATE TABLE custom_widgets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    widget_id VARCHAR(50) NOT NULL,        -- Unique ID
    name VARCHAR(100) NOT NULL,            -- Display name
    description TEXT,
    display_mode VARCHAR(20) DEFAULT 'list', -- 'list', 'table', 'grid'
    max_items INT DEFAULT 10,
    enable_alerts BOOLEAN DEFAULT TRUE,
    auto_alert BOOLEAN DEFAULT TRUE,       -- Auto-trigger on alert_active=true
    alert_aggregation VARCHAR(20) DEFAULT 'highest', -- 'highest', 'first', 'count'
    sort_column VARCHAR(50) DEFAULT 'priority',
    sort_direction VARCHAR(4) DEFAULT 'desc',
    refresh_interval INT DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_widget (user_id, widget_id)
);
```

#### Table: `custom_widget_data`
Actual data rows displayed in widget:
```sql
CREATE TABLE custom_widget_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    custom_widget_id INT NOT NULL,
    
    -- Display fields
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    description TEXT,
    icon VARCHAR(50),                      -- Emoji: '⚠️', '✅', etc.
    
    -- Linking
    link_url TEXT,                         -- External URL
    link_text VARCHAR(100),                -- Button text
    
    -- Visibility
    visible BOOLEAN DEFAULT TRUE,          -- Show/hide item
    
    -- Alerting
    alert_active BOOLEAN DEFAULT FALSE,    -- Trigger widget alert
    alert_severity VARCHAR(20),            -- 'critical', 'warning', 'info'
    alert_message VARCHAR(255),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    
    -- Styling
    highlight BOOLEAN DEFAULT FALSE,
    color VARCHAR(20),                     -- 'red', 'yellow', 'green', 'blue'
    
    -- Ordering
    priority INT DEFAULT 0,                -- Higher = top
    
    -- Custom fields
    custom_fields JSON,                    -- Extensibility
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (custom_widget_id) REFERENCES custom_widgets(id) ON DELETE CASCADE,
    INDEX idx_widget_visible (custom_widget_id, visible),
    INDEX idx_widget_priority (custom_widget_id, priority),
    INDEX idx_alert_active (custom_widget_id, alert_active)
);
```

### Data Rules

#### Visibility Rules
```sql
-- Hide item (won't display)
UPDATE custom_widget_data SET visible = false WHERE id = 123;

-- Show item
UPDATE custom_widget_data SET visible = true WHERE id = 123;
```

#### Alert Triggering Rules
```sql
-- Trigger critical alert (auto-triggers widget alert system)
UPDATE custom_widget_data 
SET alert_active = true,
    alert_severity = 'critical',
    alert_message = 'Database server is down!'
WHERE id = 123;

-- Clear alert
UPDATE custom_widget_data 
SET alert_active = false 
WHERE id = 123;

-- User acknowledges via UI → Dashboard sets:
SET acknowledged = true, acknowledged_at = NOW()
```

**Alert Severity Mapping:**
- `critical` → Red pulsing widget border (moves to top)
- `warning` → Yellow border (moves to top)
- `info` → Blue border (normal position)

#### Link Behavior Rules
```sql
-- Add clickable link
UPDATE custom_widget_data 
SET link_url = 'https://monitoring.example.com/incidents/123',
    link_text = 'View Incident'
WHERE id = 123;
```
- Opens in new tab with security (`rel="noopener noreferrer"`)

### User Workflow Example

#### Step 1: Create Widget
```sql
INSERT INTO custom_widgets (user_id, widget_id, name, enable_alerts)
VALUES (1, 'service-monitor', 'Production Services', true);
```

#### Step 2: Add Data
```sql
-- Normal item
INSERT INTO custom_widget_data (custom_widget_id, title, subtitle, icon)
VALUES (1, 'API Server', 'Status: Online', '✅');

-- Alert item
INSERT INTO custom_widget_data (
    custom_widget_id, title, subtitle, icon,
    alert_active, alert_severity, alert_message
) VALUES (
    1, 'Database', 'Status: Down', '🔴',
    true, 'critical', 'Database connection failed!'
);
```

#### Step 3: Automate Updates
```bash
#!/bin/bash
# check_service.sh - Run via cron every 5 minutes

if ! curl -sf http://api.example.com/health; then
    # Service down - trigger alert
    mysql personal_dash -e "
        UPDATE custom_widget_data 
        SET alert_active=true, 
            alert_severity='critical',
            subtitle='Status: Down',
            icon='🔴'
        WHERE title='API Server'
    "
fi
```

### API Endpoints (To Implement)

```
GET    /api/v1/custom-widgets
POST   /api/v1/custom-widgets
GET    /api/v1/custom-widgets/{widget_id}
PUT    /api/v1/custom-widgets/{widget_id}
DELETE /api/v1/custom-widgets/{widget_id}

GET    /api/v1/custom-widgets/{widget_id}/data
POST   /api/v1/custom-widgets/{widget_id}/data
PUT    /api/v1/custom-widgets/{widget_id}/data/{item_id}
DELETE /api/v1/custom-widgets/{widget_id}/data/{item_id}

POST   /api/v1/custom-widgets/{widget_id}/data/{item_id}/acknowledge
POST   /api/v1/custom-widgets/{widget_id}/data/bulk
```

### Implementation Phases

#### Phase 1: Database Schema (~2 hours)
- Create `custom_widgets` table
- Create `custom_widget_data` table
- Add Alembic migration
- Add indexes for performance

#### Phase 2: Backend API (~6-8 hours)
- CRUD endpoints for widgets
- CRUD endpoints for data
- Acknowledgment endpoint
- Bulk operations endpoint
- Visibility filtering (only fetch visible items)
- Alert aggregation logic
- User isolation (enforce user_id checks)

#### Phase 3: Frontend Widget (~6-8 hours)
- Generic `CustomWidget.jsx` component
- List display mode (default)
- Table/Grid modes (future)
- Alert triggering integration
- Acknowledgment button
- Link rendering (new tab, security)
- Icon/color/highlight styling
- Refresh mechanism
- Error handling

#### Phase 4: Documentation & Examples (~2 hours)
- User guide with examples
- Sample automation scripts (Bash, Python)
- API documentation
- Use case tutorials
- Troubleshooting guide

### What Dashboard DOES
✅ Render data according to display rules
✅ Trigger widget alerts when `alert_active = true`
✅ Handle acknowledgment when user clicks button
✅ Refresh data at configured interval
✅ Apply sorting, filtering (visible items only)
✅ Open links in new tabs with security

### What Dashboard DOES NOT DO
❌ Fetch data from external sources
❌ Run background tasks to update data
❌ Validate data logic or business rules
❌ Auto-delete old items
❌ Transform or aggregate data
❌ Send external notifications

**User responsibility:**
- Writing scripts/automation to populate data
- Scheduling data updates (cron, systemd timers)
- Data cleanup and maintenance
- External integrations
- Business logic

### Security Considerations
- ✅ Per-user data isolation (foreign key constraints)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention (React escaping)
- ✅ Safe external links (`rel="noopener noreferrer"`)
- ✅ API authentication (JWT tokens)

### Testing Plan
1. Create widget via API
2. Populate data with various field combinations
3. Test visibility toggling
4. Test alert triggering and acknowledgment
5. Test link rendering and security
6. Test sorting and prioritization
7. Test multi-user isolation
8. Load testing (many items, many widgets)

### Documentation Deliverables
- [ ] `CUSTOM_WIDGET_SPEC.md` - Complete specification ✅ **DONE**
- [ ] User guide with examples
- [ ] API reference
- [ ] Sample automation scripts
- [ ] Migration guide

### Future Enhancements (Post-MVP)
- Display modes: Table, Grid, Compact
- Custom field rendering
- Widget templates library
- Import/export functionality
- Webhook endpoints for external systems
- Rate limiting on data updates
- Data retention policies (auto-delete after N days)
- Chart/graph display mode
- Image support in items
- Rich text description formatting

---

**Complete Specification:** See `docs/CUSTOM_WIDGET_SPEC.md` for full design details, data rules, examples, and implementation guide.
