# Personal Dash - Backlog (Bugs & Enhancements)

> **Note:** This file tracks bugs and enhancement ideas for future work.

---

## Priority Summary

### High Priority (Do Next)
1. **Network Status Widget Phase 2** - Builds on completed Phase 1, adds valuable packet loss and uptime tracking
2. ~~**Stock/Crypto: Portfolio Value Graph**~~ ✅ **COMPLETED** (2026-02-13)

### Medium Priority (Soon)
3. ~~**Package Tracker: Auto-remove Delivered**~~ ✅ **COMPLETED**
4. **News: Priority Keywords** - Already partially implemented, needs UI enhancement
5. **Server Monitor: Track Specific Processes** - Already completed, but may need additional features

### Lower Priority (Later)
7. **Weather Widget Enhancements** - Nice to have additions
8. **Network Speed Test Widget** - Separate widget, different from Network Status

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
