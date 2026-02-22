# Personal Dash

A self-hosted, multi-user personal dashboard that aggregates various data sources into customizable widgets. Built with a plugin architecture for easy widget additions.

## Features

- Multi-user support with JWT authentication
- Drag-and-drop customizable widget grid
- **Widget alert system** with priority notifications and visual indicators
- Dark mode support
- Mobile responsive design
- Plugin/widget architecture for extensibility
- **Custom Widget** — push data from any script or automation via REST API
- Remote server monitoring agent

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | MySQL |
| Auth | JWT with refresh tokens |

## Project Structure

```
personal-dash/
├── frontend/       # React application
├── backend/        # FastAPI application
├── agent/          # Server monitoring agent (deploys to remote servers)
├── docs/           # Documentation and project plan
└── tests/          # Test suites
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/aboxfulloftide/personal_dash.git
cd personal_dash
```

### 2. Set up MySQL

Create the database:

```sql
CREATE DATABASE personal_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dash_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON personal_dash.* TO 'dash_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
DATABASE_URL=mysql+pymysql://dash_user:your_password@localhost:3306/personal_dash
SECRET_KEY=generate-a-random-secret-key
CORS_ORIGINS=["http://localhost:5173"]
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Run database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/api/v1/openapi.json`.

### 4. Frontend

```bash
cd frontend
npm install
```

Create your environment file:

```bash
cp .env.example .env
```

The default `VITE_API_URL=http://localhost:8000/api/v1` should work for local development.

Start the dev server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 5. Server Monitoring Agent (optional)

The monitoring agent is a standalone Python script that runs on remote servers to collect system and Docker metrics. See [agent/README.md](agent/README.md) for deployment instructions.

## Widgets

### Server Monitor
Monitor your servers' CPU, memory, disk usage, network I/O, and Docker containers.

**Features:**
- Real-time system metrics with color-coded progress bars (green/yellow/red)
- Online/offline status indicator
- Docker container list with CPU usage per container
- Configurable refresh interval (minimum 10 seconds)

**Setup:** Requires deploying the monitoring agent to each server. See [agent/README.md](agent/README.md).

---

### Package Tracker
Track packages from multiple carriers with manual entry.

**Supported Carriers:**
- USPS, UPS, FedEx, Amazon, DHL, Other

**Features:**
- Add packages with tracking number and description
- View delivery status and estimated delivery date
- Toggle to show/hide delivered packages
- Color-coded carrier badges

---

### Stock Ticker
Track stock prices and calculate your portfolio value.

**Features:**
- Add holdings with symbol and number of shares
- Real-time price and daily % change
- Portfolio total value calculation
- Remove holdings with one click

**API Providers:**
| Provider | Rate Limit | API Key |
|---|---|---|
| Alpha Vantage (default) | 25 requests/day | Optional (demo key available) |
| Finnhub | 60 requests/min | Required (free signup) |

**Rate Limiting:** Widget enforces minimum refresh intervals based on provider:
- Alpha Vantage: 5 minutes minimum
- Finnhub: 1 minute minimum

---

### Crypto Prices
Track cryptocurrency prices and calculate your portfolio value.

**Features:**
- Add holdings with coin and amount (supports decimals, e.g., 0.4931 BTC)
- Real-time price and 24h % change
- Portfolio total value in USD, EUR, or GBP
- Remove holdings with one click

**Supported Coins:** Bitcoin, Ethereum, Solana, Cardano, Dogecoin, Ripple, Polkadot, Litecoin

**API Providers:**
| Provider | Rate Limit | API Key |
|---|---|---|
| CoinGecko (default) | 10-30 requests/min | Not required |
| CoinCap | 200 requests/min | Not required |

**Rate Limiting:** Widget enforces minimum refresh intervals:
- CoinGecko: 1 minute minimum
- CoinCap: 30 seconds minimum

---

### Weather
Display current weather conditions and 5-day forecast for any location.

**Features:**
- Current temperature, feels like, humidity, and conditions
- 5-day forecast with high/low temps
- Weather icons (☀️ sunny, ⛅ partly cloudy, ☁️ cloudy, 🌧️ rainy, ❄️ snowy, ⛈️ stormy)
- Fahrenheit or Celsius display
- Automatic location geocoding (just enter city name)

**API Providers:**
| Provider | Rate Limit | API Key |
|---|---|---|
| Open-Meteo (default) | Unlimited | Not required |
| OpenWeatherMap | 1000 requests/day | Required (free signup) |

---

---

### Custom Widget

Display data from your own scripts, automation pipelines, or external tools — no frontend code required. Items are stored in the database and managed via a built-in UI. External scripts can push updates through the REST API.

**Use cases:**
- Status board fed by a cron job or CI/CD pipeline
- Home automation alerts from a shell script
- Server health summaries from a monitoring script
- Any custom data you want surfaced on your dashboard

**Features:**
- Built-in item editor (add, edit, delete, reorder by priority)
- Per-item visibility toggle without deleting
- Color-coded left border per item (red/yellow/green/blue)
- Highlight rows for emphasis
- Optional emoji icon, subtitle, description, and link
- Widget-level alerts triggered when any item has `alert_active = true`
- Per-item alert acknowledgment — suppress re-notification without deleting the item
- 4-hour cooldown prevents repeat notifications for the same alert
- Bulk push endpoint for efficiently replacing all items in one request
- Four display modes: List, Compact, Table, Grid

#### Display Modes

Configure via the widget's settings gear (⚙):

| Mode | What it shows | Best for |
|---|---|---|
| **List** | icon + title + subtitle + description + link | General purpose (default) |
| **Compact** | icon + title only, minimal padding | Many short status lines |
| **Table** | title on left, subtitle on right | Key/value pairs (service: status) |
| **Grid** | 2-column cards with icon + title + subtitle | Grouped status indicators |

#### Using the Dashboard UI

1. Add a **Custom Widget** from the widget picker
2. Click the settings gear to choose a **Display Mode**
3. Click **Manage Items** at the bottom of the widget
4. Use the form to add items — all fields except Title are optional
5. Toggle visibility per row without deleting; reorder with the Priority field (higher = top)

#### Pushing Data via the REST API

All endpoints require a Bearer token (same JWT your browser uses). Obtain one at `POST /api/v1/auth/login`.

**Base URL:** `/api/v1/custom-widgets/{widget_id}/items`

| Method | Path | Description |
|---|---|---|
| `GET` | `/{widget_id}/items` | List visible items (widget display) |
| `GET` | `/{widget_id}/items/all` | List all items including hidden (manage UI) |
| `POST` | `/{widget_id}/items` | Create one item |
| `POST` | `/{widget_id}/items/bulk` | Create multiple items at once (see below) |
| `PUT` | `/{widget_id}/items/{id}` | Update an item |
| `DELETE` | `/{widget_id}/items/{id}` | Delete one item |
| `DELETE` | `/{widget_id}/items` | Delete all items for a widget |
| `POST` | `/{widget_id}/items/{id}/acknowledge` | Acknowledge an item's alert |

**Item fields:**

| Field | Type | Description |
|---|---|---|
| `title` | string | **Required.** Main display text |
| `subtitle` | string | Secondary text shown next to title |
| `description` | string | Smaller text shown below |
| `icon` | string | Emoji displayed before the title (e.g. `"✅"`, `"⚠️"`) |
| `link_url` | string | Opens in a new tab when clicked |
| `link_text` | string | Label for the link (defaults to `→`) |
| `visible` | bool | Show/hide without deleting (default `true`) |
| `highlight` | bool | Yellow background emphasis (default `false`) |
| `color` | string | Left border color: `red`, `yellow`, `green`, `blue` |
| `priority` | int | Sort order — higher number appears first (default `0`) |
| `alert_active` | bool | Triggers a widget-level alert when `true` |
| `alert_severity` | string | `critical`, `warning`, or `info` |
| `alert_message` | string | Alert text (falls back to item title if omitted) |
| `acknowledged` | bool | Read-only. `true` after user acknowledges the alert |
| `acknowledged_at` | datetime | Read-only. Timestamp of acknowledgment |

#### Example: Python Script

```python
import requests

API = "http://localhost:8000/api/v1"

# Authenticate
token = requests.post(f"{API}/auth/login", data={
    "username": "your@email.com",
    "password": "yourpassword",
}).json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
WIDGET_ID = "widget-1234567890"  # copy from browser URL or widget settings

# Push a status item
requests.post(f"{API}/custom-widgets/{WIDGET_ID}/items", headers=headers, json={
    "title": "Build #42",
    "subtitle": "main branch",
    "icon": "✅",
    "color": "green",
    "priority": 10,
    "alert_active": False,
})
```

#### Example: Shell / curl

```bash
WIDGET_ID="widget-1234567890"
TOKEN="eyJ..."

# Create a critical alert item
curl -s -X POST "http://localhost:8000/api/v1/custom-widgets/$WIDGET_ID/items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Disk usage critical",
    "subtitle": "/dev/sda1 at 95%",
    "icon": "🔴",
    "color": "red",
    "alert_active": true,
    "alert_severity": "critical",
    "alert_message": "Disk near capacity on prod-01"
  }'

# Clear the alert once resolved
curl -s -X PUT "http://localhost:8000/api/v1/custom-widgets/$WIDGET_ID/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Disk usage OK", "icon": "✅", "color": "green", "alert_active": false}'
```

#### Bulk Push

Use `POST /{widget_id}/items/bulk` to push multiple items in a single request. Set `replace_all: true` to atomically clear existing items and replace them — the recommended pattern for cron scripts:

```bash
curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "replace_all": true,
    "items": [
      {"title": "Web Server", "subtitle": "nginx running", "icon": "✅", "color": "green", "priority": 3},
      {"title": "Database",   "subtitle": "MySQL running", "icon": "✅", "color": "green", "priority": 2},
      {"title": "Disk",       "subtitle": "42% used",      "icon": "💾", "color": "blue",  "priority": 1}
    ]
  }'
```

#### Alert Acknowledgment

When an item has `alert_active: true`, the dashboard displays a floating alert overlay with an **Acknowledge** button. Clicking it:

1. Clears the widget-level alert from the overlay
2. Marks all active alert items as `acknowledged: true` in the database
3. Stops the background scheduler from re-triggering the alert

The acknowledged state is reset automatically when an external script updates the item with `alert_active: true` again (e.g., the condition recurs on the next cron run).

You can also acknowledge individual items from the **Manage Items** modal — items with unacknowledged alerts show a clickable **alert** badge; acknowledged ones show a dimmed **ack'd** badge.

#### Example: Cron-based Status Board

A common pattern is a cron job that **bulk-replaces all items** each run:

```bash
#!/bin/bash
# /usr/local/bin/update_dash.sh — runs every 5 minutes via cron

WIDGET_ID="widget-1234567890"
TOKEN="eyJ..."
API="http://localhost:8000/api/v1"
AUTH=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

DISK=$(df -h / | awk 'NR==2{print $5}')
LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)

curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items/bulk" "${AUTH[@]}" -d "{
  \"replace_all\": true,
  \"items\": [
    {\"title\": \"Disk\", \"subtitle\": \"$DISK used\", \"icon\": \"💾\", \"priority\": 2},
    {\"title\": \"Load\", \"subtitle\": \"$LOAD\",      \"icon\": \"📊\", \"priority\": 1}
  ]
}"
```

#### Finding Your Widget ID

The widget ID is generated when you add the widget and looks like `widget-1234567890`. Find it by:
- Opening your browser dev tools → Network tab → any `GET /custom-widgets/...` request
- Or checking the dashboard layout API: `GET /api/v1/dashboard/layout`

---

### Planned Widgets

| Widget | Description |
|---|---|
| Fitness Stats | Body weight tracking with charts |
| Smart Home | Home Assistant integration |

## Widget Alert System

The dashboard includes a built-in alert system that allows widgets to display important notifications by moving to the top of the screen until acknowledged.

### Features

- **Three severity levels**: Critical (🔴), Warning (⚠️), Info (ℹ️)
- **Visual indicators**: Pulsing colored borders and alert banners
- **Automatic positioning**: Alerted widgets move to dashboard top
- **Auto-refresh**: Dashboard polls every 30 seconds to detect new alerts
- **One-click acknowledgment**: Clear alerts and return widget to original position

### Quick Start

Trigger an alert from your widget:

**Python (Backend):**
```python
from app.crud.dashboard import trigger_widget_alert

trigger_widget_alert(
    db=db,
    user_id=current_user.id,
    widget_id="widget-123456",
    severity="critical",  # "critical", "warning", or "info"
    message="Server is down!"
)
```

**JavaScript (Frontend):**
```javascript
import api from '../../services/api';

await api.post(`/widgets/${widgetId}/alert`, {
  severity: 'warning',
  message: 'Temperature exceeds threshold!'
});
```

### Testing Alerts

Use the included test script:

```bash
# List your widgets
python3 test_alert.py list-widgets

# Trigger an alert
python3 test_alert.py trigger widget-1234567890 critical "Test alert!"

# Acknowledge an alert
python3 test_alert.py acknowledge widget-1234567890
```

**Full documentation:** See [docs/WIDGET_ALERTS.md](docs/WIDGET_ALERTS.md) for complete API reference, examples, and best practices.

## Development

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

### Build for Production

```bash
cd frontend
npm run build
```

Static files will be output to `frontend/dist/` for serving via Nginx.
