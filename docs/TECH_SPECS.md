# Personal Dash - Technical Specifications

## Frontend Architecture

### Technology
- **Framework:** React 18+ with Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context + useReducer (or Zustand if needed)
- **HTTP Client:** Axios
- **Grid System:** react-grid-layout for drag-and-drop widgets

### Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── common/         # Shared components (Button, Card, Modal)
│   │   ├── layout/         # Header, Sidebar, Grid
│   │   ├── widgets/        # Individual widget components
│   │   └── auth/           # Login, Register, PasswordReset
│   ├── hooks/              # Custom React hooks
│   ├── contexts/           # React contexts (Auth, Theme, Widgets)
│   ├── services/           # API service functions
│   ├── utils/              # Helper functions
│   ├── styles/             # Global styles
│   └── App.jsx
├── public/
├── package.json
└── vite.config.js
```

### Key Features
- Responsive breakpoints: mobile (<768px), tablet (768-1024px), desktop (>1024px)
- Dark/light mode toggle with Dark mode default
- Persistent layout saved to backend per user

---

## Backend Architecture

### Technology
- **Framework:** FastAPI (Python 3.10+)
- **ORM:** SQLAlchemy 2.0
- **Database:** MySQL 8.0
- **Authentication:** JWT (access + refresh tokens)
- **Task Queue:** None for MVP (consider Celery later)
- **Email:** SMTP for password reset

### Structure
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # Route handlers
│   │       │   ├── auth.py
│   │       │   ├── users.py
│   │       │   ├── widgets.py
│   │       │   ├── servers.py
│   │       │   └── [widget].py # Per-widget endpoints
│   │       └── router.py       # API router aggregation
│   ├── core/
│   │   ├── config.py           # Settings/environment
│   │   ├── security.py         # JWT, password hashing
│   │   └── dependencies.py     # FastAPI dependencies
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   │   ├── widget_base.py      # Base widget class
│   │   └── widgets/            # Widget-specific services
│   ├── utils/                  # Helpers
│   └── main.py
├── alembic/                    # Database migrations
├── requirements.txt
└── .env.example
```

### API Versioning
All endpoints prefixed with `/api/v1/`

### Authentication Flow
1. User registers/logs in → receives access token (15 min) + refresh token (4 weeks configurable)
2. Access token in Authorization header for API calls
3. Refresh token stored in httpOnly cookie
4. Token refresh endpoint for new access tokens

---

## Database Schema

### Core Tables

```sql
-- Users
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Refresh Tokens
CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Widget Configurations (per user)
CREATE TABLE widget_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    widget_type VARCHAR(50) NOT NULL,
    config JSON,
    layout JSON,  -- Position/size in grid
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Dashboard Layouts
CREATE TABLE dashboard_layouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    layout JSON NOT NULL,  -- Full grid layout
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Server Monitoring Tables

```sql
-- Monitored Servers
CREATE TABLE servers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    hostname VARCHAR(255),
    ip_address VARCHAR(45),
    mac_address VARCHAR(17),  -- For Wake-on-LAN
    api_key_hash VARCHAR(255) NOT NULL,
    poll_interval INT DEFAULT 60,  -- seconds
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Server Metrics (time-series)
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

-- Docker Containers
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

-- Server Alerts
CREATE TABLE server_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    threshold FLOAT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- Alert History
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

### Package Tracking Tables

```sql
-- Packages
CREATE TABLE packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    tracking_number VARCHAR(100) NOT NULL,
    carrier VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    status VARCHAR(100),
    estimated_delivery DATE,
    delivered BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP,
    source VARCHAR(20) DEFAULT 'manual',  -- manual, email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Package Events
CREATE TABLE package_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL,
    status VARCHAR(255),
    location VARCHAR(255),
    event_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
);

-- Email Accounts (for parsing)
CREATE TABLE email_accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- gmail, imap
    credentials_encrypted TEXT,  -- Encrypted OAuth tokens or app passwords
    last_checked TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Widget-Specific Tables

```sql
-- Fitness/Weight Tracking
CREATE TABLE weight_entries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    unit VARCHAR(10) DEFAULT 'lbs',
    notes TEXT,
    recorded_at DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- API Cache (generic)
CREATE TABLE api_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    data JSON NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires (expires_at)
);
```

---

## Server Monitoring Agent

### Technology
- Python 3.10+
- psutil for system metrics
- docker SDK for container stats
- requests for API communication

### Features
- Configurable poll interval (default 1 min, pulled from central DB)
- Push-based communication to dashboard API
- API key authentication
- Metrics collected: CPU, memory, disk, network
- Docker container stats: status, CPU, memory, logs
- Wake-on-LAN listener

### Structure
```
agent/
├── agent.py            # Main agent script
├── collectors/
│   ├── system.py       # CPU, memory, disk, network
│   └── docker.py       # Container stats
├── config.py           # Configuration
├── requirements.txt
└── install.sh          # Installation script for systemd
```

---

## External APIs (Free Tier)

| Widget | API | Rate Limit | Cache Duration |
|--------|-----|------------|----------------|
| Stocks | Alpha Vantage | 5/min, 500/day | 1 min |
| Stocks (alt) | Finnhub | 60/min | 1 min |
| Crypto | CoinGecko | 10-50/min | 1 min |
| Weather | Open-Meteo | Unlimited | 15 min |
| Weather (alt) | OpenWeatherMap | 60/min, 1M/month | 15 min |
| News | NewsAPI | 100/day (dev) | 30 min |
| News (alt) | RSS feeds | N/A | 15 min |
| Calendar | Google Calendar API | 1M/day | 5 min |
| GitHub | GitHub API | 5000/hour (auth) | 5 min |

---

## Deployment

### Backend (systemd)
```ini
[Unit]
Description=Personal Dash API
After=network.target mysql.service

[Service]
User=personaldash
WorkingDirectory=/opt/personal-dash/backend
ExecStart=/opt/personal-dash/backend/venv/bin/uvicorn app.main:app --host 0.0.0.1 --port 9000
Restart=always
EnvironmentFile=/opt/personal-dash/backend/.env

[Install]
WantedBy=multi-user.target
```

### Frontend (Nginx)
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
        proxy_pass http://0.0.0.0:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Agent (systemd on remote servers)
```ini
[Unit]
Description=Personal Dash Monitoring Agent
After=network.target

[Service]
User=root
WorkingDirectory=/opt/personal-dash-agent
ExecStart=/opt/personal-dash-agent/venv/bin/python agent.py
Restart=always
EnvironmentFile=/opt/personal-dash-agent/.env

[Install]
WantedBy=multi-user.target
```

---

## Security Considerations

1. **Password Storage:** bcrypt hashing with salt
2. **JWT Tokens:** Short-lived access tokens (15 min), longer refresh tokens (4 weeks)
3. **API Keys:** Hashed storage for server agents
4. **CORS:** Restricted to frontend origin
5. **HTTPS:** Required in production (via Nginx/Let's Encrypt)
6. **Email Credentials:** Encrypted storage for email parsing feature
7. **Rate Limiting:** Per-user rate limits on API endpoints

---

## Testing Strategy

### Unit Tests
- All service layer functions
- Authentication flows
- Widget data processing

### Integration Tests
- API endpoint testing
- Database operations
- External API mocking

### Tools
- pytest for backend
- Jest/Vitest for frontend
- Coverage target: 80%+
