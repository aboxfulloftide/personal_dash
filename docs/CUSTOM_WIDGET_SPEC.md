# Custom Widget System - Specification

**Version:** 1.0
**Date:** February 14, 2026
**Status:** Design Specification

---

## Overview

The Custom Widget System allows users to create their own dashboard widgets **without writing code** by simply populating database tables. The dashboard handles all rendering, alerting, and interaction logic based purely on the data schema.

### Key Capabilities

- ✅ **Display custom data** - Show any data in a list/table format
- ✅ **External links** - Link items to external websites
- ✅ **Conditional visibility** - Show/hide items based on data flags
- ✅ **Alert triggering** - Automatically trigger widget alerts based on data
- ✅ **Acknowledgment** - Mark items as acknowledged to dismiss alerts
- ✅ **Automatic updates** - Widget refreshes when data changes
- ✅ **Multi-user isolation** - Each user has their own custom widget instances

### Use Cases

- Custom service monitoring (non-standard APIs)
- Business KPI dashboards (sales metrics, customer counts)
- Personal tracking (habits, goals, checklists)
- Integration with custom scripts (Bash, Python automation)
- Alert aggregation (consolidate alerts from multiple systems)
- Status boards (project status, team availability)

---

## Database Schema

### Table: `custom_widgets`

Defines the widget configuration and metadata.

```sql
CREATE TABLE custom_widgets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,

    -- Widget identification
    widget_id VARCHAR(50) NOT NULL,        -- Unique ID for dashboard integration
    name VARCHAR(100) NOT NULL,            -- Display name in widget header
    description TEXT,                       -- Optional description/subtitle

    -- Display configuration
    display_mode VARCHAR(20) DEFAULT 'list', -- 'list', 'table', 'grid', 'compact'
    max_items INT DEFAULT 10,              -- Max items to display (0 = unlimited)
    show_timestamps BOOLEAN DEFAULT TRUE,  -- Show created/updated times
    enable_links BOOLEAN DEFAULT TRUE,     -- Enable clickable links
    enable_alerts BOOLEAN DEFAULT TRUE,    -- Enable alert system

    -- Alert configuration
    auto_alert BOOLEAN DEFAULT TRUE,       -- Auto-trigger alerts when alert_active=true
    alert_aggregation VARCHAR(20) DEFAULT 'highest', -- 'highest', 'first', 'count'

    -- Sorting
    sort_column VARCHAR(50) DEFAULT 'priority', -- Column to sort by
    sort_direction VARCHAR(4) DEFAULT 'desc',   -- 'asc' or 'desc'

    -- Refresh
    refresh_interval INT DEFAULT 60,       -- Seconds between data refreshes

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_widget (user_id, widget_id),
    INDEX idx_user_id (user_id)
);
```

### Table: `custom_widget_data`

Stores the actual data rows displayed in the widget.

```sql
CREATE TABLE custom_widget_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    custom_widget_id INT NOT NULL,

    -- Display fields
    title VARCHAR(255) NOT NULL,           -- Main text displayed
    subtitle VARCHAR(255),                 -- Secondary text (optional)
    description TEXT,                       -- Full description (expandable)
    icon VARCHAR(50),                      -- Emoji or icon identifier (e.g., '⚠️', '✅')

    -- Linking
    link_url TEXT,                         -- External URL (opens in new tab)
    link_text VARCHAR(100),                -- Link button text (default: 'View')

    -- Visibility
    visible BOOLEAN DEFAULT TRUE,          -- Show/hide item

    -- Alerting
    alert_active BOOLEAN DEFAULT FALSE,    -- Trigger widget alert system
    alert_severity VARCHAR(20),            -- 'critical', 'warning', 'info'
    alert_message VARCHAR(255),            -- Alert banner message
    acknowledged BOOLEAN DEFAULT FALSE,    -- User acknowledged alert
    acknowledged_at TIMESTAMP,             -- When acknowledged

    -- Styling
    highlight BOOLEAN DEFAULT FALSE,       -- Highlight with color
    color VARCHAR(20),                     -- Color: 'red', 'yellow', 'green', 'blue', 'gray'

    -- Ordering
    priority INT DEFAULT 0,                -- Sort priority (higher = top)

    -- Custom fields (JSON for extensibility)
    custom_fields JSON,                    -- User-defined key-value pairs

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (custom_widget_id) REFERENCES custom_widgets(id) ON DELETE CASCADE,
    INDEX idx_widget_visible (custom_widget_id, visible),
    INDEX idx_widget_priority (custom_widget_id, priority),
    INDEX idx_alert_active (custom_widget_id, alert_active)
);
```

---

## Data Rules & Behavior

### 1. Visibility Rules

**How it works:**
- Items with `visible = false` are **not displayed** in the widget
- Items with `visible = true` are displayed
- No data means empty widget with "No data" message

**User control:**
```sql
-- Hide an item
UPDATE custom_widget_data SET visible = false WHERE id = 123;

-- Show an item
UPDATE custom_widget_data SET visible = true WHERE id = 123;

-- Hide all items (clears widget)
UPDATE custom_widget_data SET visible = false WHERE custom_widget_id = 1;
```

**Use cases:**
- Temporarily hide completed tasks
- Show only active alerts
- Filter based on external conditions (user script sets visible flag)

---

### 2. Alert Triggering Rules

**How it works:**

1. **Automatic Alert Triggering** (if `custom_widgets.auto_alert = true`):
   - When **any** data row has `alert_active = true` AND `acknowledged = false`
   - Widget alert is triggered with severity from `alert_severity`
   - Alert message from `alert_message` or aggregated from multiple items

2. **Alert Aggregation** (if multiple items have `alert_active = true`):
   - `highest`: Use highest severity (critical > warning > info)
   - `first`: Use first unacknowledged alert (by priority/sort order)
   - `count`: Show count of active alerts ("3 active alerts")

3. **Alert Clearing**:
   - When all alerts are acknowledged (`acknowledged = true`)
   - When all alert rows are deleted
   - When all `alert_active` flags are set to `false`

**Severity Mapping:**
| `alert_severity` | Widget Border | Visual |
|------------------|---------------|--------|
| `critical` | Red pulsing | 🔴 Moves to top |
| `warning` | Yellow | ⚠️ Moves to top |
| `info` | Blue | ℹ️ Normal position |
| (null/other) | Default | No alert |

**User control:**
```sql
-- Trigger a critical alert
INSERT INTO custom_widget_data (
    custom_widget_id,
    title,
    alert_active,
    alert_severity,
    alert_message
) VALUES (
    1,
    'Service Down',
    true,
    'critical',
    'Production server is offline!'
);

-- Clear an alert (manual)
UPDATE custom_widget_data
SET alert_active = false
WHERE id = 123;

-- Acknowledge alert (user clicks "Acknowledge" in UI)
UPDATE custom_widget_data
SET acknowledged = true, acknowledged_at = NOW()
WHERE id = 123;
```

**Use cases:**
- Service monitoring: Set `alert_active = true` when service fails health check
- Threshold alerts: Set alert when metric exceeds threshold
- Deadline reminders: Set alert when task due date approaches
- External system alerts: Ingest alerts from external monitoring tools

---

### 3. Link Behavior Rules

**How it works:**
- If `link_url` is provided, item becomes clickable
- Clicking opens URL in **new tab** (`target="_blank"`)
- If `link_text` provided, shows as button (e.g., "View Details")
- If no `link_text`, entire item is clickable

**Security:**
- All links use `rel="noopener noreferrer"` for security
- URLs can be internal (`/path`) or external (`https://...`)

**User control:**
```sql
-- Add link to item
UPDATE custom_widget_data
SET link_url = 'https://example.com/details/123',
    link_text = 'View Details'
WHERE id = 123;

-- Remove link
UPDATE custom_widget_data
SET link_url = NULL, link_text = NULL
WHERE id = 123;
```

**Use cases:**
- Link to monitoring dashboards (Grafana, Datadog)
- Link to ticketing systems (Jira, GitHub Issues)
- Link to external resources (documentation, logs)
- Link to internal tools (admin panels, reports)

---

### 4. Acknowledgment Rules

**How it works:**

1. **User Acknowledgment** (UI):
   - User clicks "Acknowledge" button on alert item
   - Dashboard calls: `POST /api/v1/custom-widgets/{widget_id}/data/{item_id}/acknowledge`
   - Sets `acknowledged = true` and `acknowledged_at = NOW()`

2. **Automatic Acknowledgment** (optional):
   - User script can auto-acknowledge when condition resolves
   - Example: Service comes back online, script sets `acknowledged = true`

3. **Alert Re-triggering**:
   - If `acknowledged = true` but `alert_active` is still `true`, alert stays acknowledged
   - To re-trigger: Set `acknowledged = false` (resets acknowledgment)

**User control:**
```sql
-- Mark as acknowledged (manual)
UPDATE custom_widget_data
SET acknowledged = true, acknowledged_at = NOW()
WHERE id = 123;

-- Reset acknowledgment (re-trigger alert)
UPDATE custom_widget_data
SET acknowledged = false
WHERE id = 123;

-- Acknowledge all alerts for widget
UPDATE custom_widget_data
SET acknowledged = true, acknowledged_at = NOW()
WHERE custom_widget_id = 1 AND alert_active = true;
```

---

### 5. Display Customization Rules

**Icon Field:**
- Accepts emoji (e.g., `⚠️`, `✅`, `🔴`, `📊`)
- Displayed before title
- Optional, no icon if null

**Color Field:**
- Values: `red`, `yellow`, `green`, `blue`, `gray`, `purple`, `orange`
- Applies background highlight to item
- Used with `highlight = true` for emphasis

**Highlight Field:**
- `true`: Apply colored background
- `false`: Normal appearance

**Custom Fields (JSON):**
- Store arbitrary key-value pairs
- Not displayed by default widget
- Available for future custom renderers
- Example: `{"status": "active", "count": 42, "tags": ["prod", "critical"]}`

**User control:**
```sql
-- Style an item
UPDATE custom_widget_data
SET icon = '⚠️',
    color = 'yellow',
    highlight = true
WHERE id = 123;

-- Add custom fields
UPDATE custom_widget_data
SET custom_fields = '{"status": "degraded", "response_time_ms": 2500}'
WHERE id = 123;
```

---

### 6. Sorting & Ordering Rules

**Default sort order:**
1. `priority` (descending - highest first)
2. `created_at` (descending - newest first)

**User-configurable sort:**
```sql
-- Configure widget to sort by created_at
UPDATE custom_widgets
SET sort_column = 'created_at', sort_direction = 'desc'
WHERE id = 1;

-- Configure widget to sort by title alphabetically
UPDATE custom_widgets
SET sort_column = 'title', sort_direction = 'asc'
WHERE id = 1;
```

**Priority values:**
- Higher numbers = higher priority (shown first)
- Negative numbers allowed
- Default: 0

**User control:**
```sql
-- Set high priority (show first)
UPDATE custom_widget_data SET priority = 100 WHERE id = 123;

-- Set low priority (show last)
UPDATE custom_widget_data SET priority = -10 WHERE id = 456;
```

---

## User Workflow

### Step 1: Create Custom Widget Instance

```sql
INSERT INTO custom_widgets (
    user_id,
    widget_id,
    name,
    description,
    display_mode,
    max_items,
    enable_alerts,
    refresh_interval
) VALUES (
    1,                          -- Your user ID
    'my-service-monitor',       -- Unique widget ID
    'Service Monitor',          -- Display name
    'Monitors critical services', -- Description
    'list',                     -- Display mode
    20,                         -- Show max 20 items
    true,                       -- Enable alerts
    30                          -- Refresh every 30 seconds
);
```

### Step 2: Add Widget to Dashboard

**Option A: Via API**
```bash
curl -X POST http://localhost:8000/api/v1/custom-widgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "widget_id": "my-service-monitor",
    "name": "Service Monitor",
    "display_mode": "list",
    "enable_alerts": true
  }'
```

**Option B: Via Frontend**
- Open "Add Widget" dialog
- Select "Custom Widget"
- Choose from your custom widgets list
- Widget appears on dashboard

### Step 3: Populate Data

```sql
-- Add a normal item
INSERT INTO custom_widget_data (
    custom_widget_id,
    title,
    subtitle,
    icon,
    link_url,
    visible,
    priority
) VALUES (
    1,                                  -- custom_widget.id
    'Web Server',
    'Status: Online',
    '✅',
    'https://example.com/status',
    true,
    10
);

-- Add an alert item
INSERT INTO custom_widget_data (
    custom_widget_id,
    title,
    subtitle,
    icon,
    alert_active,
    alert_severity,
    alert_message,
    color,
    highlight,
    priority
) VALUES (
    1,
    'Database Server',
    'Status: Down',
    '🔴',
    true,                              -- Trigger alert
    'critical',                        -- Red pulsing border
    'Database connection failed!',
    'red',
    true,
    100                                -- High priority
);
```

### Step 4: Update Data (Automation)

**Example: Bash script monitoring service**
```bash
#!/bin/bash
# monitor_service.sh - Check service and update widget

WIDGET_ID=1
DB_HOST="localhost"
DB_USER="dash_user"
DB_NAME="personal_dash"

# Check if service is up
if curl -sf http://example.com/health > /dev/null; then
    # Service is up - clear alert
    mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "
        UPDATE custom_widget_data
        SET alert_active = false,
            subtitle = 'Status: Online',
            icon = '✅',
            color = 'green',
            updated_at = NOW()
        WHERE custom_widget_id = $WIDGET_ID
        AND title = 'Web Service';
    "
else
    # Service is down - trigger alert
    mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "
        UPDATE custom_widget_data
        SET alert_active = true,
            alert_severity = 'critical',
            alert_message = 'Web service health check failed!',
            subtitle = 'Status: Down',
            icon = '🔴',
            color = 'red',
            highlight = true,
            acknowledged = false,
            priority = 100,
            updated_at = NOW()
        WHERE custom_widget_id = $WIDGET_ID
        AND title = 'Web Service';
    "
fi
```

**Run via cron:**
```cron
*/5 * * * * /path/to/monitor_service.sh
```

### Step 5: Acknowledge Alerts (User)

**Via Dashboard UI:**
1. User sees red pulsing widget at top of dashboard
2. Clicks "Acknowledge" button on alert item
3. Alert is marked acknowledged
4. Widget returns to normal position (if all alerts cleared)

**Via Database (manual):**
```sql
UPDATE custom_widget_data
SET acknowledged = true, acknowledged_at = NOW()
WHERE id = 123;
```

---

## API Endpoints (To Be Implemented)

### Widget Management

```
GET    /api/v1/custom-widgets
       List user's custom widgets

POST   /api/v1/custom-widgets
       Create new custom widget

GET    /api/v1/custom-widgets/{widget_id}
       Get widget configuration

PUT    /api/v1/custom-widgets/{widget_id}
       Update widget configuration

DELETE /api/v1/custom-widgets/{widget_id}
       Delete widget and all data
```

### Data Management

```
GET    /api/v1/custom-widgets/{widget_id}/data
       Get all data items (filtered by visible=true)

POST   /api/v1/custom-widgets/{widget_id}/data
       Create new data item

GET    /api/v1/custom-widgets/{widget_id}/data/{item_id}
       Get specific data item

PUT    /api/v1/custom-widgets/{widget_id}/data/{item_id}
       Update data item

DELETE /api/v1/custom-widgets/{widget_id}/data/{item_id}
       Delete data item

POST   /api/v1/custom-widgets/{widget_id}/data/{item_id}/acknowledge
       Mark item as acknowledged
```

### Bulk Operations

```
POST   /api/v1/custom-widgets/{widget_id}/data/bulk
       Bulk create/update/delete items

POST   /api/v1/custom-widgets/{widget_id}/data/acknowledge-all
       Acknowledge all active alerts
```

---

## Example Use Cases

### 1. Service Health Monitor

**Setup:**
- Widget: "Production Services"
- Data rows: One per service (API, DB, Redis, etc.)
- Script: Runs every minute, checks health endpoints
- Behavior: Sets `alert_active=true` when health check fails

**Data example:**
```sql
-- Initial data
INSERT INTO custom_widget_data (custom_widget_id, title, subtitle, icon, link_url) VALUES
(1, 'API Server', 'Status: Online', '✅', 'https://api.example.com/health'),
(1, 'Database', 'Status: Online', '✅', 'https://db.example.com/status'),
(1, 'Redis Cache', 'Status: Online', '✅', 'https://redis.example.com');

-- When API fails (set by script)
UPDATE custom_widget_data
SET alert_active = true,
    alert_severity = 'critical',
    alert_message = 'API server health check failed',
    subtitle = 'Status: Down',
    icon = '🔴',
    color = 'red',
    highlight = true
WHERE title = 'API Server';
```

---

### 2. Sales KPI Dashboard

**Setup:**
- Widget: "Today's Metrics"
- Data rows: Daily sales count, revenue, new customers
- Script: Runs hourly, queries database/CRM
- Behavior: Highlights items that exceed goals

**Data example:**
```sql
INSERT INTO custom_widget_data (custom_widget_id, title, subtitle, icon, color, highlight) VALUES
(2, 'Sales Today', '42 orders ($3,200)', '💰', 'green', true),  -- Exceeds goal
(2, 'New Customers', '8 signups', '👥', 'blue', false),
(2, 'Conversion Rate', '3.2%', '📊', 'yellow', true);  -- Below goal
```

---

### 3. Task/Reminder System

**Setup:**
- Widget: "Action Items"
- Data rows: Tasks with due dates
- Script: Runs daily, checks due dates
- Behavior: Sets alert when task is overdue

**Data example:**
```sql
-- Overdue task
INSERT INTO custom_widget_data (
    custom_widget_id, title, subtitle, icon,
    alert_active, alert_severity, alert_message,
    color, highlight, link_url
) VALUES (
    3,
    'Submit monthly report',
    'Due: 2 days ago',
    '⚠️',
    true,
    'warning',
    'Overdue task: Submit monthly report',
    'yellow',
    true,
    'https://docs.example.com/monthly-reports'
);

-- Upcoming task (not urgent)
INSERT INTO custom_widget_data (
    custom_widget_id, title, subtitle, icon, color, link_url
) VALUES (
    3,
    'Review Q1 budget',
    'Due: in 5 days',
    '📋',
    'blue',
    'https://finance.example.com/budget'
);
```

---

### 4. External Alert Aggregator

**Setup:**
- Widget: "All Alerts"
- Data rows: Alerts from multiple monitoring systems
- Script: Polls external APIs, writes to custom_widget_data
- Behavior: Aggregates all alerts in one place

**Data example:**
```sql
-- PagerDuty alert
INSERT INTO custom_widget_data (
    custom_widget_id, title, subtitle, description,
    alert_active, alert_severity, alert_message,
    link_url, link_text, icon
) VALUES (
    4,
    'High CPU on prod-web-01',
    'Source: PagerDuty',
    'CPU usage: 95% for 10 minutes',
    true,
    'critical',
    'Critical: High CPU alert from PagerDuty',
    'https://mycompany.pagerduty.com/incidents/12345',
    'View Incident',
    '🔥'
);

-- Datadog alert
INSERT INTO custom_widget_data (
    custom_widget_id, title, subtitle,
    alert_active, alert_severity,
    link_url, link_text, icon
) VALUES (
    4,
    'High error rate',
    'Source: Datadog',
    true,
    'warning',
    'https://app.datadoghq.com/monitors/12345',
    'View Monitor',
    '⚠️'
);
```

---

## Display Modes (Future Enhancement)

### List Mode (Default)
```
┌─────────────────────────────────┐
│ Service Monitor           [≡]   │
├─────────────────────────────────┤
│ ✅  API Server                  │
│     Status: Online       [Link] │
├─────────────────────────────────┤
│ 🔴  Database Server             │
│     Status: Down         [Link] │
│     ⚠️ Database failed!          │
│     [Acknowledge]                │
└─────────────────────────────────┘
```

### Compact Mode
```
┌─────────────────────────────────┐
│ Service Monitor           [≡]   │
├─────────────────────────────────┤
│ ✅ API Server        │ 🔴 DB     │
│ ✅ Redis             │ ✅ Queue  │
└─────────────────────────────────┘
```

### Table Mode
```
┌─────────────────────────────────────────┐
│ Service Monitor                   [≡]   │
├──────────┬─────────┬─────────┬──────────┤
│ Service  │ Status  │ Icon    │ Action   │
├──────────┼─────────┼─────────┼──────────┤
│ API      │ Online  │ ✅      │ [Link]   │
│ Database │ Down    │ 🔴      │ [Ack]    │
└──────────┴─────────┴─────────┴──────────┘
```

---

## Constraints & Limitations

### What Users MUST Do
1. ✅ Create `custom_widgets` entry for each widget instance
2. ✅ Populate `custom_widget_data` with their data
3. ✅ Set `alert_active`, `alert_severity` to trigger alerts
4. ✅ Set `visible = false` to hide items
5. ✅ Manage data freshness (delete old items, update existing)

### What Dashboard WILL Do
1. ✅ Render data according to display rules
2. ✅ Trigger widget alerts when `alert_active = true`
3. ✅ Handle acknowledgment when user clicks button
4. ✅ Refresh data at configured interval
5. ✅ Apply sorting, filtering (visible items only)
6. ✅ Open links in new tabs with security attributes

### What Dashboard WILL NOT Do
1. ❌ Fetch data from external sources
2. ❌ Run background tasks to update data
3. ❌ Validate data logic or business rules
4. ❌ Auto-delete old items
5. ❌ Transform or aggregate data
6. ❌ Send external notifications (email, Slack, etc.)

**User responsibility:**
- Writing scripts/automation to populate data
- Scheduling data updates (cron, systemd timers)
- Data cleanup and maintenance
- External integrations
- Business logic

---

## Security Considerations

### Data Isolation
- Each user can only see their own `custom_widgets`
- Foreign key constraints enforce ownership
- API endpoints check `user_id` matches authenticated user

### SQL Injection
- All API endpoints use parameterized queries (SQLAlchemy ORM)
- Direct database access by user scripts is their responsibility

### XSS Prevention
- All user-provided text (title, subtitle, description) HTML-escaped by React
- URLs validated before rendering
- Icon field restricted to emoji/text (no HTML)

### Link Safety
- All external links use `rel="noopener noreferrer"`
- Links open in new tab to prevent navigation hijacking
- No JavaScript URLs allowed

---

## Migration Path

### Phase 1: Database Schema
- Create `custom_widgets` and `custom_widget_data` tables
- Add Alembic migration

### Phase 2: Backend API
- CRUD endpoints for widgets and data
- Acknowledgment endpoint
- Data filtering (visible items only)

### Phase 3: Frontend Widget
- Generic `CustomWidget.jsx` component
- Render based on `display_mode`
- Alert triggering integration
- Acknowledgment button

### Phase 4: Documentation
- User guide with examples
- API documentation
- Sample scripts (Bash, Python)

### Phase 5: Enhancements (Optional)
- Table/Grid display modes
- Custom field rendering
- Widget templates library
- Import/export functionality

---

## Next Steps

1. **Review this specification** - Confirm design meets requirements
2. **Database migration** - Create tables and indexes
3. **Backend implementation** - API endpoints and CRUD logic
4. **Frontend implementation** - Generic widget component
5. **Testing** - Create sample widgets and automation scripts
6. **Documentation** - User guide with examples

---

**Questions to Consider:**

1. Should users be able to create widgets via UI, or only via API/database?
2. Should we provide webhook endpoints for external systems to push data?
3. Should we add rate limiting on data updates to prevent abuse?
4. Should we add data retention policies (auto-delete after N days)?
5. Should we provide sample scripts/templates for common use cases?

---

**Document Version:** 1.0
**Status:** Design Specification - Awaiting Approval
**Author:** Development Team
**Date:** February 14, 2026
