# Personal Dash - Backlog (Bugs & Enhancements)

> **Note:** This file tracks bugs and enhancement ideas for future work. Items are not prioritized - just captured for later consideration.

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

#### Database Caching for API Results
**Status:** Not Started
**Priority:** High
**Description:**
Stock and Crypto widgets sometimes show blank data, likely due to hitting API rate limits. Need to implement database caching as a fallback.

**Current Problem:**
- Crypto widget occasionally shows blank/empty
- Likely hitting rate limits on free API tiers
- No fallback when API fails or is throttled

**Proposed Solution:**
1. Store API results in database with timestamp
2. Cache results once per hour (avoid excessive DB writes)
3. When API call fails or returns no data, read most recent cached data from database
4. Display cached data with a timestamp indicator (e.g., "Last updated: 45 minutes ago")

**Technical Implementation:**
- Create new database tables:
  - `stock_cache` (symbol, price, change, volume, timestamp, user_id)
  - `crypto_cache` (symbol, price, change, market_cap, timestamp, user_id)
- Add caching logic to API endpoints:
  - Check if we have data from last hour in DB
  - If yes, use cached data
  - If no or stale (>1 hour), fetch from API and update cache
- On API failure, always fall back to most recent cached data
- Add "last updated" timestamp to widget display

**Benefits:**
- Resilient to API outages and rate limits
- Reduces API calls (better for free tier limits)
- Always shows data (even if slightly stale)
- Better user experience

**Related Files:**
- `backend/app/api/v1/endpoints/stocks.py`
- `backend/app/api/v1/endpoints/crypto.py`
- `backend/app/models/` (new cache models)
- Database migration needed

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

#### Monitor Mounted Drives Status
**Status:** Not Started
**Priority:** Medium
**Description:**
Display status of mounted drives (NAS mounts, external drives, network shares).

**Requirements:**
- Show all mounted filesystems
- For each mount:
  - Mount point (e.g., `/mnt/nas`, `/media/backup`)
  - Device/source (e.g., `//nas/share`, `/dev/sdb1`)
  - Filesystem type (ext4, nfs, cifs, etc.)
  - Status: Mounted ✓ / Not mounted ✗
  - Disk usage (used/total, %)
- Alert when expected mounts are missing
- Allow user to configure which mounts to track

**Technical Implementation:**
- Agent side (Python):
  - Add `get_mount_status()` function
  - Use `psutil.disk_partitions()` to get all mounts
  - Filter for specific mount points configured by user
  - Collect usage stats with `psutil.disk_usage()`
  - Detect missing expected mounts
- Backend:
  - Update server configuration to store expected mount points
  - Add mount status to agent data response
- Frontend:
  - Add "Mounts" section to server monitor widget
  - Show table of mount points with status
  - Highlight missing/unmounted drives in red
  - Add setting to configure expected mount points

**Use Cases:**
- Monitor NAS mounts (ensure network shares are connected)
- Track external backup drives
- Verify game server data drives are mounted
- Alert if critical mounts fail

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

## General / Other Widgets

_(Add more items here as needed)_

---

## Completed Items

_(Move items here when completed)_
