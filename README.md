# Personal Dash

A self-hosted, multi-user personal dashboard that aggregates various data sources into customizable widgets. Built with a plugin architecture for easy widget additions.

## Features

- Multi-user support with JWT authentication
- Drag-and-drop customizable widget grid
- **Widget alert system** with priority notifications and visual indicators
- Dark mode support
- Mobile responsive design
- Plugin/widget architecture for extensibility
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

### Planned Widgets

| Widget | Description |
|---|---|
| Fitness Stats | Body weight tracking with charts |
| Calendar | Google Calendar integration |
| News Headlines | RSS/News API aggregation |
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
