# Widget Alert System

The Widget Alert System allows any widget to display important notifications by temporarily moving to the top of the dashboard with visual indicators until acknowledged by the user.

## Features

- **Three severity levels**: Critical (🔴), Warning (⚠️), Info (ℹ️)
- **Visual indicators**: Pulsing colored borders and alert banners
- **Automatic positioning**: Alerted widgets move to top of dashboard
- **Priority sorting**: Multiple alerts stack by severity (critical first)
- **Position restoration**: Widgets return to original position after acknowledgment
- **Auto-refresh**: Dashboard polls every 30 seconds to detect new alerts

## How It Works

1. **Trigger**: Widget or external system calls the alert API endpoint
2. **Display**: Widget jumps to top with pulsing border and alert banner
3. **Acknowledge**: User clicks "Acknowledge" button
4. **Restore**: Widget smoothly returns to its original position

## Using Alerts in Your Widget

### Method 1: From Backend (Python)

If your widget has a backend data endpoint, you can trigger alerts directly:

```python
from fastapi import APIRouter, Depends
from app.api.v1.deps import CurrentActiveUser, DbSession
import requests

router = APIRouter()

@router.get("/widgets/my-widget/data")
def get_my_widget_data(current_user: CurrentActiveUser, db: DbSession):
    # Your widget logic here
    data = fetch_some_data()

    # Check for alert conditions
    if data['status'] == 'critical':
        # Trigger an alert
        trigger_widget_alert(
            db=db,
            user_id=current_user.id,
            widget_id="widget-123456789",  # Your widget's ID
            severity="critical",
            message="Server is down!"
        )

    return data


# Alternative: Use the API endpoint directly
def trigger_alert_via_api(widget_id: str, severity: str, message: str, token: str):
    """Trigger alert by calling the API endpoint"""
    import requests

    response = requests.post(
        f"http://localhost:8000/api/v1/widgets/{widget_id}/alert",
        json={
            "severity": severity,
            "message": message
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()
```

### Method 2: From Frontend (JavaScript/React)

Trigger alerts from your widget component:

```javascript
import api from '../../services/api';

function MyWidget({ config, widgetId }) {
  const checkStatus = async () => {
    const data = await fetchData();

    // Check for alert conditions
    if (data.temperature > 100) {
      // Trigger alert
      await api.post(`/widgets/${widgetId}/alert`, {
        severity: 'warning',
        message: 'Temperature exceeds safe threshold: ' + data.temperature + '°C'
      });
    }
  };

  return (
    <div>
      {/* Your widget UI */}
    </div>
  );
}
```

### Method 3: From External Scripts

Use the provided test script or create your own:

```bash
# Using the test script
python3 test_alert.py trigger widget-1234567890 critical "Database connection lost!"

# Using curl
curl -X POST "http://localhost:8000/api/v1/widgets/WIDGET_ID/alert" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"severity": "critical", "message": "Alert message here"}'
```

## API Reference

### Trigger Alert

**Endpoint:** `POST /api/v1/widgets/{widget_id}/alert`

**Request Body:**
```json
{
  "severity": "critical",  // "critical", "warning", or "info"
  "message": "Alert message text"
}
```

**Response:**
```json
{
  "success": true,
  "widget_id": "widget-1234567890",
  "alert_active": true,
  "severity": "critical",
  "message": "Alert message text"
}
```

### Acknowledge Alert

**Endpoint:** `POST /api/v1/widgets/{widget_id}/acknowledge`

**Response:**
```json
{
  "success": true,
  "widget_id": "widget-1234567890",
  "alert_active": false,
  "severity": null,
  "message": null
}
```

## Severity Levels

| Severity | Icon | Color | Use Case |
|----------|------|-------|----------|
| `critical` | 🔴 | Red | System failures, urgent issues requiring immediate attention |
| `warning` | ⚠️ | Orange | Potential problems, threshold breaches, non-critical issues |
| `info` | ℹ️ | Blue | Informational updates, completion notifications, FYI messages |

## Example: Server Monitor Widget

Here's a complete example of integrating alerts into a widget:

### Backend (Python)

```python
# backend/app/api/v1/endpoints/widgets/server_monitor.py
from fastapi import APIRouter, HTTPException
from app.api.v1.deps import CurrentActiveUser, DbSession
from app.crud.dashboard import trigger_widget_alert, get_widget_from_dashboard

router = APIRouter()

@router.get("/widgets/server-monitor/data")
def get_server_data(
    widget_id: str,
    current_user: CurrentActiveUser,
    db: DbSession
):
    # Get widget config
    widget = get_widget_from_dashboard(db, current_user.id, widget_id)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    server_ip = widget['config'].get('server_ip', 'localhost')

    # Check server status
    is_online = ping_server(server_ip)

    # Trigger alert if server is down
    if not is_online:
        trigger_widget_alert(
            db=db,
            user_id=current_user.id,
            widget_id=widget_id,
            severity="critical",
            message=f"Server {server_ip} is not responding!"
        )

    return {
        "server_ip": server_ip,
        "status": "online" if is_online else "offline",
        "last_check": datetime.now().isoformat()
    }
```

### Frontend (React)

```javascript
// frontend/src/components/widgets/ServerMonitorWidget.jsx
import { useWidgetData } from '../../hooks/useWidgetData';

export default function ServerMonitorWidget({ config, widgetId }) {
  const { data, loading, error } = useWidgetData(
    `/widgets/server-monitor/data?widget_id=${widgetId}`,
    60000  // Check every 60 seconds
  );

  if (loading) return <div>Checking server...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h3>Server: {data.server_ip}</h3>
      <p className={data.status === 'online' ? 'text-green-600' : 'text-red-600'}>
        Status: {data.status}
      </p>
      <p className="text-xs text-gray-500">
        Last check: {new Date(data.last_check).toLocaleTimeString()}
      </p>
    </div>
  );
}
```

## Testing Alerts

### Test Script

The project includes a test script for triggering and managing alerts:

```bash
# List all widgets
python3 test_alert.py list-widgets

# Trigger a critical alert
python3 test_alert.py trigger widget-1234567890 critical "Test critical alert!"

# Trigger a warning
python3 test_alert.py trigger widget-1234567890 warning "Test warning"

# Trigger an info alert
python3 test_alert.py trigger widget-1234567890 info "Test info message"

# Acknowledge an alert
python3 test_alert.py acknowledge widget-1234567890
```

### Setup for Testing

1. Get your auth token from the browser:
   - Login to the dashboard
   - Open DevTools (F12)
   - Go to Application → Local Storage
   - Copy the `token` value

2. Set the token as an environment variable:
   ```bash
   export AUTH_TOKEN='your_token_here'
   ```

3. Run the test script:
   ```bash
   python3 test_alert.py list-widgets
   ```

## Best Practices

### When to Use Alerts

✅ **Good use cases:**
- System failures or critical errors
- Threshold breaches (temperature, disk space, etc.)
- Security events
- Delivery notifications
- Completion of long-running tasks

❌ **Avoid alerts for:**
- Regular status updates (use normal widget display)
- Frequently changing data
- Non-actionable information
- Routine events

### Alert Frequency

- **Don't spam**: Avoid triggering the same alert repeatedly
- **Debounce**: Wait before re-alerting for the same condition
- **Clear previous alerts**: Acknowledge old alerts before triggering new ones for the same issue

### Message Guidelines

- **Be specific**: "Server web-01 is down" not "Server error"
- **Include context**: "Temperature: 105°C (max: 100°C)"
- **Actionable**: Tell the user what's wrong or what happened
- **Concise**: Keep messages under 100 characters when possible

### Example: Debouncing Alerts

```python
from datetime import datetime, timedelta

# Track last alert time per widget
last_alert_times = {}

def should_trigger_alert(widget_id: str, cooldown_minutes: int = 5) -> bool:
    """Prevent alert spam by enforcing a cooldown period"""
    last_alert = last_alert_times.get(widget_id)

    if last_alert is None:
        return True

    cooldown = timedelta(minutes=cooldown_minutes)
    return datetime.now() - last_alert > cooldown

def trigger_alert_with_cooldown(db, user_id, widget_id, severity, message):
    """Trigger alert only if cooldown period has passed"""
    if should_trigger_alert(widget_id):
        trigger_widget_alert(db, user_id, widget_id, severity, message)
        last_alert_times[widget_id] = datetime.now()
        return True
    return False
```

## Troubleshooting

### Alert not appearing

1. **Check polling**: Alerts appear within 30 seconds. Wait or refresh the page.
2. **Check widget ID**: Ensure you're using the correct widget ID
3. **Check auth**: Verify your token is valid
4. **Check console**: Look for errors in browser DevTools

### Alert stuck/won't acknowledge

1. **Check network**: Ensure acknowledge API call succeeds
2. **Refresh page**: Hard refresh (Ctrl+Shift+R)
3. **Check backend logs**: Look for errors in backend console

### Multiple widgets showing

If widgets appear duplicated or layout is broken:
1. Run the fix script: `python3 fix_layout.py`
2. Refresh the dashboard

## Database Schema

Alert data is stored in the `dashboard_layouts` table as part of the JSON `layout` column:

```json
{
  "widgets": [
    {
      "id": "widget-1234567890",
      "type": "server_monitor",
      "config": { ... },
      "alert_active": true,
      "alert_severity": "critical",
      "alert_message": "Server is down!",
      "alert_triggered_at": "2026-02-12T19:30:00Z",
      "original_layout_x": 5,
      "original_layout_y": 10
    }
  ],
  "layout": [ ... ]
}
```

## Architecture Notes

- **No database migrations needed**: Alert fields are stored in existing JSON column
- **Automatic cleanup**: Alert fields are cleared when acknowledged
- **Position tracking**: Original widget position is saved before moving to top
- **Layout isolation**: Edit mode uses original layout, not adjusted layout
- **Polling mechanism**: Dashboard refreshes every 30 seconds to detect new alerts
- **No layout saves during adjustments**: Prevents infinite loops when alerts are triggered/acknowledged

## Future Enhancements

Potential improvements for the alert system:

- [ ] WebSocket support for instant alerts (no 30-second delay)
- [ ] Auto-dismiss after timeout (e.g., info alerts auto-clear after 5 minutes)
- [ ] Alert history/log
- [ ] Sound notifications
- [ ] Email/SMS integration for critical alerts
- [ ] Alert counts in dashboard header
- [ ] Snooze functionality
- [ ] Custom severity levels per widget type
