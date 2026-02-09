# Internet Speed Test & Connection Status Widget

## Overview
Create a widget that monitors internet connection status, performs speed tests on demand or schedule, and displays historical connection data. Useful for monitoring ISP performance and troubleshooting connectivity issues.

## Features

### 1. Connection Status (Real-time)
**Current connection health and basic metrics**

#### Display Elements:
- **Status Indicator**
  - 🟢 Online - Connected, all good
  - 🟡 Degraded - Connected but slow/high latency
  - 🔴 Offline - No connection
  - 🟠 Limited - Connected but no internet access

- **Connection Info**
  - Current IP address (public IPv4/IPv6)
  - ISP name and location
  - Connection type (if detectable: Fiber, Cable, DSL, etc.)
  - Uptime (time since last disconnection)

- **Quick Metrics**
  - Ping/Latency to common servers (Google DNS, Cloudflare)
  - Jitter (ping stability)
  - Packet loss percentage

### 2. Speed Test (On-Demand & Scheduled)
**Measure download, upload, and latency**

#### Test Capabilities:
- **Download Speed** (Mbps)
- **Upload Speed** (Mbps)
- **Ping/Latency** (ms)
- **Jitter** (ms)
- **Test Server** (closest/selected server location)

#### Test Options:
- Manual "Run Test" button
- Scheduled tests (hourly, daily, weekly)
- Quick test (smaller data transfer, faster)
- Full test (larger data transfer, more accurate)
- Test to specific server (dropdown selection)

### 3. Historical Data & Graphs
**Track performance over time**

#### Data Visualization:
- **Line Graph** - Speed over time (last 24h, 7d, 30d)
- **Min/Max/Avg** - Speed statistics for time period
- **Reliability Score** - Percentage of time meeting expected speeds
- **Outage Log** - List of disconnection events with duration

#### Historical Views:
- Last 10 tests (table view)
- Daily average speeds (chart)
- Peak vs off-peak performance
- Speed test results export (CSV)

## Technical Implementation

### Backend Architecture

#### Data Sources:

**Option A: Ookla Speedtest CLI** (Recommended)
- Official Speedtest by Ookla command-line tool
- Most accurate, industry standard
- Free for personal use
- Install: `curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash && sudo apt-get install speedtest`
- Usage: `speedtest --format=json`
- Provides: download, upload, ping, jitter, server info, ISP

**Option B: LibreSpeed** (Self-hosted alternative)
- Open-source speed test server
- No external dependencies
- Requires self-hosted speed test server
- Good for internal network testing

**Option C: Fast.com API** (Netflix)
- Simple, Netflix CDN-based
- Only measures download speed
- No official API, would need scraping

**Option D: Custom Implementation**
- Download/upload test files from known servers
- Measure transfer rates
- More control but less accurate

**Recommendation: Ookla Speedtest CLI** - Industry standard, accurate, easy to integrate

#### Connection Status Sources:

**Ping Tests:**
- Ping multiple reliable hosts:
  - `8.8.8.8` (Google DNS)
  - `1.1.1.1` (Cloudflare DNS)
  - `208.67.222.222` (OpenDNS)
- Average latency, packet loss, jitter

**Public IP Detection:**
- API: `https://api.ipify.org?format=json`
- Alternative: `https://ifconfig.me/ip`
- Includes geolocation and ISP info

**ISP Information:**
- API: `https://ipapi.co/{ip}/json/`
- Returns: ISP name, city, country, ASN
- Free tier: 1000 requests/day

### Backend API Endpoints

```python
# Get current connection status
GET /api/v1/network/status
Response: {
  "status": "online",  # online, degraded, offline, limited
  "ip_address": "1.2.3.4",
  "isp": "Comcast Cable",
  "location": "San Francisco, CA",
  "latency_avg": 15.2,
  "jitter": 2.1,
  "packet_loss": 0.0,
  "uptime_seconds": 86400,
  "last_check": "2026-02-07T12:00:00Z"
}

# Run speed test
POST /api/v1/network/speedtest
Body: {
  "server_id": 12345,  # Optional: specific test server
  "test_type": "full"  # quick or full
}
Response: {
  "id": 123,
  "download_mbps": 345.67,
  "upload_mbps": 42.31,
  "ping_ms": 12.4,
  "jitter_ms": 1.2,
  "server": "San Francisco, CA",
  "isp": "Comcast Cable",
  "timestamp": "2026-02-07T12:00:00Z"
}

# Get speed test history
GET /api/v1/network/speedtest/history
Query: {
  "days": 7,  # Last N days
  "limit": 50  # Max results
}
Response: {
  "tests": [...],
  "stats": {
    "avg_download": 350.2,
    "avg_upload": 41.8,
    "min_download": 280.1,
    "max_download": 389.5
  }
}

# Get outage log
GET /api/v1/network/outages
Query: {
  "days": 30
}
Response: {
  "outages": [
    {
      "start": "2026-02-05T03:15:00Z",
      "end": "2026-02-05T03:47:00Z",
      "duration_seconds": 1920
    }
  ]
}

# Update speed test schedule
PUT /api/v1/network/speedtest/schedule
Body: {
  "enabled": true,
  "frequency": "daily",  # hourly, daily, weekly
  "time": "02:00"  # 2 AM daily
}
```

### Database Schema

```python
class SpeedTest(Base):
    __tablename__ = "speed_tests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    download_mbps = Column(Float)
    upload_mbps = Column(Float)
    ping_ms = Column(Float)
    jitter_ms = Column(Float, nullable=True)
    server_name = Column(String(255))
    server_id = Column(Integer, nullable=True)
    isp = Column(String(255), nullable=True)
    test_type = Column(String(20))  # quick, full, scheduled
    created_at = Column(DateTime, server_default=func.now())


class NetworkStatus(Base):
    __tablename__ = "network_status"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20))  # online, degraded, offline
    ip_address = Column(String(45), nullable=True)
    isp = Column(String(255), nullable=True)
    latency_ms = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)
    packet_loss_pct = Column(Float, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    # Index on user_id and timestamp for efficient queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


class SpeedTestSchedule(Base):
    __tablename__ = "speedtest_schedules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    enabled = Column(Boolean, default=False)
    frequency = Column(String(20))  # hourly, daily, weekly
    time_of_day = Column(String(5), nullable=True)  # "02:00"
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
```

### Frontend Components

#### Widget Layout

```
┌─────────────────────────────────────────┐
│ 🟢 Online                  [Run Test]  │
├─────────────────────────────────────────┤
│  Download    Upload      Ping           │
│  ↓ 345 Mbps  ↑ 42 Mbps   12 ms         │
├─────────────────────────────────────────┤
│ ISP: Comcast Cable                      │
│ IP: 1.2.3.4 • Uptime: 1d 3h            │
├─────────────────────────────────────────┤
│ [Speed History Graph - Last 7 Days]    │
│         ⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯                     │
│        /    \  /\                       │
│       /      \/  \___                   │
├─────────────────────────────────────────┤
│ Last test: 2 hours ago                  │
│ Next scheduled: Today at 11:00 PM      │
└─────────────────────────────────────────┘
```

#### States

**1. Idle State**
- Show last test results
- Connection status indicator
- "Run Test" button enabled

**2. Testing State**
- Animated spinner/progress indicator
- "Testing..." message
- Show which phase: "Testing download..." "Testing upload..."
- Disable "Run Test" button

**3. Error State**
- Show error message
- Suggest troubleshooting (check connection, try again)
- "Retry" button

**4. Historical View**
- Toggle between current and historical
- Date range selector
- Graph view options (line chart, bar chart)

### Widget Settings

```javascript
{
  "connection_check_interval": 60,  // seconds, for status monitoring
  "schedule_enabled": false,
  "schedule_frequency": "daily",
  "schedule_time": "02:00",
  "alert_on_slow_speed": false,
  "alert_threshold_mbps": 100,  // Alert if below this
  "preferred_server_id": null,  // null = auto-select
  "show_historical_graph": true,
  "graph_period": "7d",  // 24h, 7d, 30d
  "test_type": "full"  // quick or full
}
```

## Background Service (Scheduler)

### Implementation Options:

**Option A: Backend Scheduler (APScheduler)**
- Run scheduled speed tests in background
- Monitor connection status periodically
- Store results in database
- Lightweight, integrated with FastAPI

**Option B: Systemd Timer**
- Separate systemd service for speed tests
- More reliable for long-running schedules
- Independent of web server

**Recommendation: APScheduler** - Easier to manage, integrated with app

### Scheduler Tasks:

1. **Connection Status Monitor** (every 60 seconds)
   - Ping test to multiple hosts
   - Detect online/offline/degraded states
   - Log state changes (for outage tracking)

2. **Scheduled Speed Tests** (user-configured)
   - Run full speed test at scheduled time
   - Store results in database
   - Optional: Send notification if speeds are below threshold

3. **Cleanup Task** (daily)
   - Remove network status logs older than 30 days
   - Aggregate old speed test data (monthly averages)

## User Experience Enhancements

### Speed Test Features:
- **Compare to ISP Promise**: Show if speeds meet advertised plan
  - User sets expected speeds in settings
  - Widget shows "Meeting 95% of promised speed" ✅ or "Below expected" ⚠️

- **Best/Worst Times**: Identify when internet is fastest/slowest
  - "Your internet is typically fastest at 3 AM"
  - "Peak slowdown occurs at 8 PM"

- **Export Results**: Download speed test history as CSV
  - For ISP complaints or troubleshooting
  - Include timestamps, speeds, server locations

### Connection Status Features:
- **Outage Notifications**: Alert when connection drops
  - Browser notification (if permissions granted)
  - Log outage duration for review

- **Quality Indicator**: Beyond just online/offline
  - Green: Excellent (low latency, no packet loss)
  - Yellow: Degraded (high latency or packet loss)
  - Red: Poor (very high latency, significant packet loss)

- **Multi-Device View** (future): If multiple servers monitored
  - Show which devices/servers are online
  - Useful for monitoring remote servers

## Security & Privacy Considerations

### Privacy:
- Speed tests reveal IP address to test servers (Ookla, etc.)
- Store minimal PII (IP addresses are optional in DB)
- Allow users to disable IP logging

### Rate Limiting:
- Limit speed tests to avoid abuse
  - Max 1 test per 5 minutes
  - Max 10 tests per day per user
- Scheduled tests don't count against manual limit

### Resource Usage:
- Speed tests use bandwidth (10-100 MB per full test)
- Option for "quick test" (5-10 MB)
- Warn user before running test on metered connections

## Implementation Phases

### Phase 1: Basic Connection Status (2-3 hours)
1. Backend endpoint for current connection status
2. Ping test implementation (latency, packet loss)
3. Public IP detection
4. Frontend widget showing status and metrics
5. Widget settings for check interval

### Phase 2: Speed Test On-Demand (3-4 hours)
1. Install and test Speedtest CLI
2. Backend endpoint to trigger speed test
3. Parse and store speed test results in database
4. Frontend "Run Test" button with loading state
5. Display test results in widget
6. Add speed test history view

### Phase 3: Scheduled Speed Tests (2-3 hours)
1. Implement APScheduler in backend
2. Database schema for schedules
3. Endpoint to configure schedule
4. Background job to run scheduled tests
5. Frontend settings for schedule configuration

### Phase 4: Historical Data & Graphs (3-4 hours)
1. Backend endpoint for historical data with aggregation
2. Frontend chart library integration (Chart.js or Recharts)
3. Graph component with time period selector
4. Statistics calculations (min/max/avg)
5. Export functionality (CSV download)

### Phase 5: Advanced Features (4-6 hours)
1. ISP speed comparison (vs. promised speeds)
2. Outage detection and logging
3. Alert system for slow speeds
4. Best/worst time analysis
5. Connection quality indicators

## Dependencies

### Backend:
- **Speedtest CLI** (Ookla) - Binary installation
- **APScheduler** - `pip install apscheduler`
- No new Python packages needed (httpx, subprocess already available)

### Frontend:
- **Chart.js** or **Recharts** (~50KB) - For historical graphs
- **react-chartjs-2** - React wrapper for Chart.js

## Performance Considerations

### Backend:
- Speed tests should run asynchronously (don't block API)
- Use background tasks/threads for long operations
- Cache connection status for 60 seconds (reduce ping spam)

### Frontend:
- Don't auto-run speed tests on widget load (user-initiated only)
- Lazy load historical data (only when graph expanded)
- Debounce rapid "Run Test" clicks

### Database:
- Index on user_id + timestamp for fast queries
- Consider archiving old data (>90 days) to separate table
- Aggregate old data to reduce storage (daily averages after 30 days)

## Future Enhancements

- **Network Device Scanner**: Scan local network for connected devices
- **Bandwidth Monitor**: Track real-time bandwidth usage (requires agent)
- **VPN Detection**: Show if VPN is active and where endpoint is located
- **DNS Speed Test**: Compare DNS resolver speeds
- **Traceroute Visualization**: Show network path to destinations
- **Mobile Data Toggle**: Skip tests when on mobile hotspot
- **ISP Outage Map**: Show if others in area experiencing issues
- **Compare to Neighbors**: Anonymized speed comparison in your area

## Estimated Total Effort
- **Phase 1 (Basic Status):** 2-3 hours
- **Phase 2 (Speed Test):** 3-4 hours
- **Phase 3 (Scheduling):** 2-3 hours
- **Phase 4 (Historical Data):** 3-4 hours
- **Phase 5 (Advanced):** 4-6 hours
- **Total:** 14-20 hours

## Priority
**Medium** - Nice to have for power users and those monitoring ISP performance. Not critical for basic dashboard functionality but provides unique value for troubleshooting connectivity.

## Alternative: Simplified Version
If full implementation is too complex, consider a minimal version:
- Just current connection status (ping test)
- Manual speed test button (no scheduling)
- Last 3 test results (no graphs)
- Estimated effort: 4-6 hours
