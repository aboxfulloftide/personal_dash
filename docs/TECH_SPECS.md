# Personal Dash - Technical Specifications

**Last Updated:** February 14, 2026
**Version:** 2.0 (Reflects current implementation)

---

## Frontend Architecture

### Technology Stack
- **Framework:** React 18+ with Vite 5
- **Styling:** Tailwind CSS 3.x
- **State Management:** React Context + useReducer
- **HTTP Client:** Axios
- **Grid System:** react-grid-layout for drag-and-drop widgets
- **Mapping:** Leaflet + react-leaflet (for weather radar)
- **Charts:** (Planned for fitness/portfolio widgets)

### Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── common/         # Shared components (Button, Card, Modal)
│   │   ├── layout/         # Header, Sidebar, Grid, AlertBanner
│   │   ├── widgets/        # Individual widget components
│   │   │   ├── widgetRegistry.js
│   │   │   ├── WidgetContainer.jsx
│   │   │   ├── ServerMonitorWidget.jsx
│   │   │   ├── PackageTrackerWidget.jsx
│   │   │   ├── WeatherWidget.jsx
│   │   │   ├── StockTickerWidget.jsx
│   │   │   ├── CryptoWidget.jsx
│   │   │   ├── NewsWidget.jsx
│   │   │   ├── CalendarWidget.jsx
│   │   │   ├── NetworkStatusWidget.jsx
│   │   │   └── PortfolioGraph.jsx
│   │   └── auth/           # Login, Register, PasswordReset
│   ├── hooks/              # Custom React hooks (useWidgetData, etc.)
│   ├── contexts/           # React contexts (Auth, Theme)
│   ├── services/           # API service functions (api.js)
│   ├── utils/              # Helper functions
│   ├── styles/             # Global styles
│   └── App.jsx
├── public/
├── package.json
└── vite.config.js
```

### Key Features
- **Responsive Design:** Mobile (<768px), Tablet (768-1024px), Desktop (>1024px)
- **Dark Mode:** Default dark theme with light mode toggle
- **Persistent Layout:** Saved to backend per user via dashboard_layouts table
- **Lazy Loading:** Widgets loaded on-demand for code splitting
- **Widget Alert System:** Visual notifications with auto-positioning
- **Silent Background Refresh:** Updates without loading states to minimize flashing

---

## Backend Architecture

### Technology Stack
- **Framework:** FastAPI 0.128+ (Python 3.12)
- **ORM:** SQLAlchemy 2.0
- **Database:** MySQL 8.0
- **Authentication:** JWT (access 15min + refresh 4 weeks tokens)
- **Background Tasks:** APScheduler 3.10 (asyncio)
- **Email:** IMAP via imapclient for package scanning
- **Encryption:** Fernet (cryptography) for email credentials
- **Network Testing:** speedtest-cli, subprocess ping

### Structure
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/          # Route handlers
│   │       │   ├── auth.py
│   │       │   ├── dashboard.py    # Layout, widget alerts
│   │       │   ├── servers.py
│   │       │   ├── packages.py
│   │       │   ├── email_credentials.py
│   │       │   ├── email_scanner.py
│   │       │   ├── weather.py      # Weather + alerts
│   │       │   ├── finance.py      # Stocks + crypto
│   │       │   ├── news.py
│   │       │   ├── calendar.py
│   │       │   └── network.py      # Ping + speed tests
│   │       ├── deps.py             # FastAPI dependencies
│   │       └── router.py           # API router aggregation
│   ├── core/
│   │   ├── config.py               # Settings/environment
│   │   ├── security.py             # JWT, password hashing
│   │   ├── encryption.py           # Fernet encryption
│   │   ├── database.py             # SQLAlchemy setup
│   │   └── scheduler.py            # APScheduler tasks
│   ├── models/                     # SQLAlchemy models
│   │   ├── user.py
│   │   ├── widget.py               # WidgetConfig, DashboardLayout
│   │   ├── server.py
│   │   ├── package.py
│   │   ├── network.py
│   │   └── finance.py
│   ├── schemas/                    # Pydantic schemas
│   ├── crud/                       # Database operations
│   │   ├── dashboard.py            # Widget alert triggers
│   │   ├── package.py
│   │   ├── email_credential.py
│   │   ├── network.py
│   │   ├── speedtest.py
│   │   └── finance.py
│   ├── utils/
│   │   ├── email_parser.py         # Tracking number extraction
│   │   └── speedtest_utils.py      # Network testing
│   └── main.py
├── alembic/                        # Database migrations
├── requirements.txt
└── .env
```

### API Versioning
All endpoints prefixed with `/api/v1/`

### Authentication Flow
1. User registers/logs in → receives access token (15 min) + refresh token (4 weeks)
2. Access token in `Authorization: Bearer {token}` header for API calls
3. Refresh token stored in httpOnly cookie
4. `/auth/refresh` endpoint for new access tokens
5. Token rotation on refresh for enhanced security

---

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);
```

#### Authentication
```sql
CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token_hash),
    INDEX idx_expires (expires_at)
);

CREATE TABLE password_reset_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Widget System

#### Widget Configuration
```sql
CREATE TABLE widget_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    widget_type VARCHAR(50) NOT NULL,
    config JSON,                        -- Widget settings
    layout JSON,                        -- Position/size in grid
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Widget Alert System
    alert_active BOOLEAN DEFAULT FALSE,
    alert_severity VARCHAR(20),         -- 'critical', 'warning', 'info'
    alert_message TEXT,
    alert_triggered_at TIMESTAMP,
    original_layout_x INT,              -- Store position before alert move
    original_layout_y INT,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, widget_type)
);

CREATE TABLE dashboard_layouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    layout JSON NOT NULL,               -- Full grid layout with widgets array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Server Monitoring

```sql
CREATE TABLE servers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    hostname VARCHAR(255),
    ip_address VARCHAR(45),
    mac_address VARCHAR(17),            -- For Wake-on-LAN
    api_key_hash VARCHAR(255) NOT NULL,
    poll_interval INT DEFAULT 60,       -- seconds
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE server_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    cpu_percent FLOAT,
    memory_percent FLOAT,
    disk_percent FLOAT,
    network_in BIGINT,
    network_out BIGINT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    INDEX idx_server_recorded (server_id, recorded_at)
);

CREATE TABLE docker_containers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    container_id VARCHAR(64) NOT NULL,
    name VARCHAR(255),
    image VARCHAR(255),
    status VARCHAR(50),
    cpu_percent FLOAT,
    memory_usage BIGINT,
    memory_limit BIGINT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE monitored_processes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    process_name VARCHAR(255) NOT NULL,
    pattern VARCHAR(255),               -- Regex pattern for matching
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE monitored_drives (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    mount_point VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE server_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,    -- 'cpu', 'memory', 'disk', 'offline'
    threshold FLOAT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE TABLE alert_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_id INT NOT NULL,
    triggered_value FLOAT,
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES server_alerts(id) ON DELETE CASCADE
);
```

### Package Tracking

```sql
CREATE TABLE packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    tracking_number VARCHAR(100) NOT NULL,
    carrier VARCHAR(50) NOT NULL,       -- 'usps', 'ups', 'fedex', 'amazon'
    description VARCHAR(255),
    status VARCHAR(100),
    estimated_delivery DATE,
    delivered BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP,
    dismissed BOOLEAN DEFAULT FALSE,    -- Soft delete
    dismissed_at TIMESTAMP,

    -- Email scanning metadata
    email_source VARCHAR(255),          -- Email address it was found in
    email_subject TEXT,                 -- Original subject line
    email_sender VARCHAR(255),          -- Sender email
    email_date TIMESTAMP,               -- When email was received
    email_body_snippet TEXT,            -- Preview text
    tracking_url TEXT,                  -- Direct link to carrier tracking

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_tracking (user_id, tracking_number),
    INDEX idx_delivered (delivered, dismissed)
);

CREATE TABLE package_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL,
    status VARCHAR(255),
    location VARCHAR(255),
    event_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
);

CREATE TABLE email_credentials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    imap_server VARCHAR(255) NOT NULL,
    imap_port INT NOT NULL DEFAULT 993,
    encrypted_password TEXT NOT NULL,   -- Fernet encrypted
    auto_scan_enabled BOOLEAN DEFAULT FALSE,
    scan_interval_hours INT DEFAULT 12,
    days_to_scan INT DEFAULT 7,         -- How far back to scan
    last_scan_at TIMESTAMP,
    last_scan_status VARCHAR(50),
    last_scan_message TEXT,
    last_scan_packages_found INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_email (user_id, email_address)
);
```

### Reminders

```sql
CREATE TABLE reminders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    notes TEXT,

    -- Recurrence settings
    recurrence_type VARCHAR(20) NOT NULL,  -- 'interval', 'day_of_week'
    interval_value INT,                    -- For interval: 4 (every 4 hours/days/etc)
    interval_unit VARCHAR(20),             -- 'hours', 'days', 'weeks', 'months'
    days_of_week VARCHAR(20),              -- For day_of_week: '0,1,2,3,4' (Mon-Fri)
    reminder_time TIME,                    -- Time for the reminder

    start_date DATE NOT NULL,
    carry_over BOOLEAN DEFAULT TRUE,       -- Show next day if missed vs auto-dismiss
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_active (user_id, is_active)
);

CREATE TABLE reminder_instances (
    id INT PRIMARY KEY AUTO_INCREMENT,
    reminder_id INT NOT NULL,
    user_id INT NOT NULL,
    due_date DATE NOT NULL,
    due_time TIME,
    instance_number INT,                   -- For hourly reminders (1, 2, 3, etc.)
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'dismissed', 'missed'
    dismissed_at TIMESTAMP,
    is_overdue BOOLEAN DEFAULT FALSE,      -- Carried over from previous day
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_due_date_status (user_id, due_date, status),
    INDEX idx_reminder_due (reminder_id, due_date)
);
```

### Network Monitoring

```sql
CREATE TABLE network_targets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    host VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_host (user_id, host)
);

CREATE TABLE speed_test_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    download_mbps FLOAT,
    upload_mbps FLOAT,
    ping_ms FLOAT,
    server_name VARCHAR(255),
    server_location VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_timestamp (user_id, timestamp)
);
```

### Finance Tracking

```sql
CREATE TABLE stock_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(12, 2),
    change_percent DECIMAL(8, 4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_symbol (user_id, symbol),
    INDEX idx_updated (last_updated)
);

CREATE TABLE crypto_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    coin_id VARCHAR(50) NOT NULL,       -- 'bitcoin', 'ethereum', etc.
    price DECIMAL(18, 8),
    change_24h DECIMAL(8, 4),
    market_cap BIGINT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_coin (user_id, coin_id),
    INDEX idx_updated (last_updated)
);
```

### Caching

```sql
CREATE TABLE api_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    data JSON NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key (cache_key),
    INDEX idx_expires (expires_at)
);
```

---

## Background Task Scheduler

### Technology
- **APScheduler 3.10** (AsyncIO scheduler)
- Runs in FastAPI application lifespan
- Supports interval, cron, and date triggers

### Scheduled Tasks

| Task | Interval | Description |
|------|----------|-------------|
| **Email Auto-Scan** | 30 minutes | Scan user email accounts for tracking numbers |
| **Package Cleanup** | 30 minutes | Remove delivered packages at midnight next day |
| **Speed Test Cleanup** | Daily | Delete speed test results older than 90 days |
| **Weather Alerts Monitor** | 5 minutes | Check for severe weather and trigger widget alerts |
| **Reminders Midnight Reset** | 30 minutes | Mark missed/overdue reminders, generate daily instances |

### Task Details

#### Email Auto-Scan
```python
# Scans IMAP accounts for users with auto_scan_enabled=True
# Extracts tracking numbers from common shippers
# Creates packages automatically
# Marks delivered packages based on confirmation emails
```

#### Package Cleanup
```python
# Finds packages with delivered=True and dismissed=False
# Removes packages at midnight the day after delivery
# Uses local timezone (not UTC) for "midnight" calculation
```

#### Weather Alerts Monitor
```python
# Queries all users with weather widgets
# Fetches NWS alerts for each location
# Triggers widget alerts for Extreme/Severe + Immediate/Expected
# Maps NWS severity to widget severity (critical/warning/info)
# Auto-clears widget alerts when weather threat ends
```

---

## Widget System

### Available Widgets

| Widget | Type | Category | Size | Features |
|--------|------|----------|------|----------|
| **Server Monitor** | `server_monitor` | Monitoring | 3×3 | CPU, RAM, disk, Docker containers, processes, drives |
| **Package Tracker** | `package_tracker` | Lifestyle | 3×3 | Track shipments, email scanning, delivery notifications |
| **Weather** | `weather` | Lifestyle | 3×4 | Current, hourly, 5-day, radar, severe alerts |
| **Stock Ticker** | `stock_ticker` | Finance | 3×3 | Real-time quotes, portfolio tracking |
| **Crypto Prices** | `crypto_prices` | Finance | 3×3 | Cryptocurrency prices, portfolio tracking |
| **News Headlines** | `news_headlines` | Lifestyle | 3×3 | RSS feeds, keyword filtering, NewsAPI support |
| **Calendar** | `calendar` | Lifestyle | 3×3 | ICS/iCal events, smart view selection |
| **Network Status** | `network_status` | Monitoring | 3×2 | Multi-site ping, speed tests, uptime tracking |
| **Reminders** | `reminders` | Lifestyle | 3×3 | Recurring reminders, daily/weekly/interval schedules, carry-over |
| **Portfolio Graph** | `portfolio_graph` | Finance | 3×3 | (Planned) Historical portfolio charts |

### Widget Alert System

#### How It Works
1. **Triggering:** Backend calls `trigger_widget_alert(user_id, widget_id, severity, message)`
2. **Visual Changes:**
   - Widget gets colored pulsing border (red/yellow/blue)
   - Widget moves to top-left of dashboard (x=0, y=0)
   - Original position stored in `original_layout_x/y`
   - Alert banner appears in widget header
3. **User Acknowledgment:** Click "Acknowledge" button
4. **Clearing:** Widget returns to original position, alert removed

#### Severity Levels
- **Critical:** Red pulsing border (tornadoes, extreme weather, server down)
- **Warning:** Yellow border (severe weather, high resource usage)
- **Info:** Blue border (moderate weather, informational alerts)

#### Automatic Triggers
- **Weather Widget:** Severe weather detected (NWS Extreme/Severe + Immediate/Expected)
- **Server Monitor:** (Planned) Server offline, resource thresholds exceeded
- **Package Tracker:** (Planned) Delivery exceptions, delayed packages

---

## External APIs

### Weather
| API | Purpose | Rate Limit | Cache | Key Required |
|-----|---------|------------|-------|--------------|
| **Open-Meteo** | Weather forecasts | Unlimited | 15 min | No |
| **OpenWeatherMap** | Weather (alternative) | 60/min, 1M/month | 15 min | Yes |
| **RainViewer** | Precipitation radar | Unlimited | 5 min | No |
| **National Weather Service** | Severe weather alerts | No documented limit | 5 min | No (US only) |

### Finance
| API | Purpose | Rate Limit | Cache | Key Required |
|-----|---------|------------|-------|--------------|
| **Yahoo Finance** | Stock quotes | Unlimited (unofficial) | 20 min | No |
| **Alpha Vantage** | Stock quotes | 25/day (free) | 20 min | Yes |
| **Finnhub** | Stock quotes | 60/min (free) | 20 min | Yes |
| **CoinGecko** | Crypto prices | 10-50/min | 20 min | Optional |
| **CoinCap** | Crypto prices | Unlimited | 20 min | No |

### News & Calendar
| API | Purpose | Rate Limit | Cache | Key Required |
|-----|---------|------------|-------|--------------|
| **RSS Feeds** | News aggregation | N/A | 15 min | No |
| **NewsAPI.org** | News headlines | 100/day (dev) | 30 min | Yes |
| **ICS/iCal** | Calendar events | N/A | 5 min | No |

### Geocoding
| API | Purpose | Rate Limit | Cache | Key Required |
|-----|---------|------------|-------|--------------|
| **Open-Meteo Geocoding** | Location search | Unlimited | N/A | No |

---

## Server Monitoring Agent

### Technology
- Python 3.10+
- **psutil** for system metrics
- **docker SDK** for container stats
- **requests** for API communication

### Features
- Configurable poll interval (default 60s, pulled from dashboard)
- Push-based communication to dashboard API
- API key authentication
- Metrics collected: CPU, memory, disk, network I/O
- Docker container stats: status, CPU, memory
- Process monitoring: Check if specific processes are running
- Drive monitoring: Track specific mount points
- Wake-on-LAN listener (planned)

### Structure
```
agent/
├── dash_agent.py       # Main agent script
├── collectors/
│   ├── system.py       # CPU, memory, disk, network
│   └── docker.py       # Container stats
├── config.py           # Configuration
└── requirements.txt
```

### Configuration
```ini
[Server]
api_url = https://dash.example.com/api/v1
api_key = <server-api-key>
server_id = 1
poll_interval = 60
```

### Deployment (systemd)
```ini
[Unit]
Description=Personal Dash Monitoring Agent
After=network.target

[Service]
User=root
WorkingDirectory=/opt/dash-agent
ExecStart=/opt/dash-agent/venv/bin/python dash_agent.py
Restart=always
EnvironmentFile=/opt/dash-agent/.env

[Install]
WantedBy=multi-user.target
```

---

## Deployment

### Backend (systemd)
```ini
[Unit]
Description=Personal Dash API
After=network.target mysql.service

[Service]
User=matheau
WorkingDirectory=/home/matheau/code/personal_dash_claude/backend
ExecStart=/home/matheau/miniforge3/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/matheau/code/personal_dash_claude/backend/.env

[Install]
WantedBy=multi-user.target
```

### Frontend (Development - Vite)
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### Frontend (Production - Nginx)
```nginx
server {
    listen 80;
    server_name dash.example.com;

    root /opt/personal-dash/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Setup
```bash
# Create database
mysql -u root -p
CREATE DATABASE personal_dash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dash_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON personal_dash.* TO 'dash_user'@'localhost';
FLUSH PRIVILEGES;

# Run migrations
cd backend
alembic upgrade head
```

---

## Security Considerations

### Authentication & Credentials
1. **Password Storage:** bcrypt hashing with automatic salt
2. **JWT Tokens:**
   - Access tokens: 15 minutes (short-lived)
   - Refresh tokens: 4 weeks (configurable)
   - Token rotation on refresh
3. **API Keys:** SHA-256 hashed storage for server agents
4. **Email Credentials:** Fernet symmetric encryption (cryptography library)
5. **Session Management:** Refresh token invalidation on logout

### Network Security
1. **CORS:** Restricted to frontend origin (configurable in .env)
2. **HTTPS:** Required in production (via Nginx/Let's Encrypt)
3. **Headers:** Security headers (HSTS, X-Frame-Options, CSP)
4. **Rate Limiting:** Per-user rate limits on sensitive endpoints (planned)

### Data Protection
1. **SQL Injection:** Prevented via SQLAlchemy ORM
2. **XSS:** React's built-in escaping
3. **CSRF:** Not applicable (no cookies for auth, JWT in headers)
4. **Secrets Management:** Environment variables (.env), never committed

### Monitoring & Logging
1. **Error Tracking:** Uvicorn logs, FastAPI exception handlers
2. **Access Logs:** Nginx access logs
3. **Audit Trail:** Created_at/updated_at timestamps on all tables

---

## Testing Strategy

### Backend Testing
- **Unit Tests:** Service layer functions, CRUD operations
- **Integration Tests:** API endpoints, database operations
- **External API Mocking:** httpx.AsyncClient mocking
- **Framework:** pytest, pytest-asyncio
- **Coverage Target:** 80%+

### Frontend Testing
- **Unit Tests:** Component logic, utility functions
- **Integration Tests:** Widget data flows, API integration
- **E2E Tests:** User workflows (planned)
- **Framework:** Vitest, React Testing Library
- **Coverage Target:** 80%+

### Test Files
```
backend/
└── tests/
    ├── test_auth.py
    ├── test_widgets.py
    ├── test_weather.py
    └── test_packages.py

frontend/
└── src/
    └── __tests__/
        ├── components/
        └── utils/
```

---

## Development Workflow

### Environment Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with database credentials
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Database Migrations
```bash
cd backend
# Create new migration
alembic revision --autogenerate -m "description"
# Review migration file in alembic/versions/
# Apply migration
alembic upgrade head
# Rollback
alembic downgrade -1
```

### Adding New Widgets
1. Create component: `frontend/src/components/widgets/NewWidget.jsx`
2. Register in: `frontend/src/components/widgets/widgetRegistry.js`
3. Add backend endpoint: `backend/app/api/v1/endpoints/new_widget.py`
4. Add models/schemas if needed
5. Update CRUD operations
6. Test widget data flow

---

## Performance Optimization

### Backend
- **Database Connection Pooling:** SQLAlchemy pool (5-20 connections)
- **API Caching:** api_cache table for expensive external API calls
- **Async Operations:** httpx.AsyncClient for external APIs
- **Background Tasks:** APScheduler offloads long-running tasks
- **Query Optimization:** Indexes on frequently queried columns

### Frontend
- **Code Splitting:** Lazy loading via dynamic imports for widgets
- **Silent Refresh:** Background data updates without loading states
- **Debouncing:** Grid layout saves debounced to prevent excessive API calls
- **Memoization:** React.memo for expensive components
- **Bundle Size:** Vite tree-shaking, production builds

### Network
- **HTTP/2:** Enabled via Nginx
- **Compression:** Gzip/Brotli for static assets
- **CDN:** (Planned) for static assets
- **WebSockets:** (Planned) for real-time server metrics

---

## Monitoring & Observability

### Health Checks
- **Backend:** `GET /health` endpoint
- **Database:** Connection pool monitoring
- **External APIs:** Circuit breaker pattern (planned)

### Metrics
- **Response Times:** Uvicorn logs
- **Error Rates:** FastAPI exception tracking
- **Resource Usage:** Server monitoring agent
- **Background Tasks:** APScheduler job execution logs

### Logging
```python
# Backend logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## Future Enhancements

### In Design Phase
- [ ] **Custom Widget System** - Generic database-driven widgets (see [CUSTOM_WIDGET_SPEC.md](CUSTOM_WIDGET_SPEC.md))
  - Users populate database tables, dashboard renders automatically
  - Supports display, links, visibility control, alerts, acknowledgment
  - Use cases: service monitoring, KPI dashboards, task tracking, alert aggregation

### Planned Features
- [ ] Mobile app (React Native)
- [ ] Push notifications (web push API)
- [ ] Multi-language support (i18n)
- [ ] Advanced analytics dashboard
- [ ] Export/import dashboard layouts
- [ ] Shared dashboards (read-only links)
- [ ] Integration marketplace (Zapier-like)
- [ ] Advanced charting (recharts/d3.js)
- [ ] Voice commands (Web Speech API)

### Widget Ideas
- [ ] Fitness tracking (Apple Health, Fitbit sync)
- [ ] Smart home controls (Home Assistant)
- [ ] Music player (Spotify, Last.fm)
- [ ] GitHub contributions graph
- [ ] RSS reader with full articles
- [ ] Todo list (Todoist, Things sync)
- [ ] System clipboard manager
- [ ] Terminal emulator widget

---

## Dependencies

### Backend Core
```
fastapi==0.128.0
uvicorn==0.40.0
sqlalchemy==2.0.46
pymysql==1.1.2
alembic==1.18.3
pydantic==2.12.5
pydantic-settings==2.12.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.2.1
```

### Backend Features
```
httpx==0.28.1                  # Async HTTP client
apscheduler==3.10.4            # Background task scheduler
cryptography==46.0.4           # Email credential encryption
imapclient==3.0.1              # Email scanning
feedparser==6.0.11             # RSS parsing
icalendar==6.0.1               # Calendar parsing
recurring-ical-events==3.8.0   # Recurring event expansion
speedtest-cli==2.1.3           # Network speed testing
```

### Frontend
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.2",
  "react-grid-layout": "^1.4.4",
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.1",
  "@headlessui/react": "^1.7.17",
  "@heroicons/react": "^2.1.1"
}
```

---

**Document Version:** 2.0
**Last Updated:** February 14, 2026
**Maintained By:** Development Team
