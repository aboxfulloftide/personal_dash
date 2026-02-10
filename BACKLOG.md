# Feature Backlog & Enhancement Ideas

This document tracks planned features and enhancements for the Personal Dashboard.

---

## Network Status Widget - Future Enhancements

### Phase 2: Speed Testing & Historical Data (High Priority)

**Speed Tests**
- [ ] Integrate speed test API (LibreSpeed, fast.com API, or Ookla)
- [ ] Implement download/upload speed measurements
- [ ] Show current vs average speeds
- [ ] Add on-demand "Run Speed Test" button
- [ ] Display bandwidth usage trends

**Historical Graphs**
- [ ] Create line charts for latency trends over time
- [ ] Visualize packet loss history
- [ ] Calculate and display connection uptime percentage
- [ ] Add expandable graph section (similar to weather radar pattern)
- [ ] Time range selector (1h, 6h, 24h, 7d, 30d)

### Phase 3: Alerts & Monitoring (Medium Priority)

**Connection Event Tracking**
- [ ] Log status changes (online → degraded → offline) in database
- [ ] Display recent connection events with timestamps
- [ ] Track and display total downtime duration
- [ ] Show connection stability metrics

**Notifications**
- [ ] Email/webhook alerts when connection degrades
- [ ] Configurable alert thresholds (latency, packet loss)
- [ ] Daily/weekly summary reports via email
- [ ] Integration with notification services (Discord, Slack, etc.)

### Phase 4: Advanced Diagnostics (Lower Priority)

**Enhanced Metrics**
- [ ] Measure DNS resolution time per target
- [ ] Add HTTP response time tests (not just ICMP ping)
- [ ] Track jitter trends and analysis
- [ ] MTR/traceroute path visualization
- [ ] Identify routing issues

**Comparison & Analysis**
- [ ] Compare multiple time periods
- [ ] Identify patterns (slowest time of day, weekly trends)
- [ ] Export historical data as CSV
- [ ] Generate PDF reports

### Quick Wins (Easy Additions)

- [ ] Target presets: Quick-add buttons for common services
  - Google (8.8.8.8), Cloudflare (1.1.1.1), OpenDNS (208.67.222.222)
  - Discord, AWS, Azure, GitHub, Netflix, Twitch
- [ ] Color-code latency ranges
  - Green: <50ms (Excellent)
  - Yellow: 50-150ms (Good)
  - Orange: 150-300ms (Fair)
  - Red: >300ms (Poor)
- [ ] Configurable ping count (currently hardcoded to 4)
- [ ] Compact vs detailed view toggle
- [ ] Target grouping/categories (DNS Servers, Gaming, Services, etc.)
- [ ] Sort targets by latency, name, or status
- [ ] Favorite/pin specific targets to top

---

## Other Widget Ideas

### Network Speed & Connection Status Widget
Status: Phase 1 Complete ✅
- [x] Multi-site ping monitoring
- [x] Public IP and ISP detection
- [x] Configurable ping targets
- [x] Connection status (online/degraded/offline)
- [x] Latency, jitter, and packet loss metrics

---

## General Dashboard Improvements

### Performance
- [ ] Implement widget lazy loading for faster initial page load
- [ ] Add service worker for offline support
- [ ] Optimize dashboard save operations (debounce)

### User Experience
- [ ] Dark mode improvements and theme customization
- [ ] Widget templates/presets for common setups
- [ ] Import/export dashboard layout
- [ ] Keyboard shortcuts for common actions
- [ ] Mobile-responsive widget layouts

### Backend
- [ ] Database cleanup tasks (auto-delete old metrics)
- [ ] Rate limiting for API endpoints
- [ ] Caching layer for frequently accessed data
- [ ] Background job queue for heavy operations

---

## Completed Features

### 2026-02-09
- ✅ Network Status Widget - Phase 1 (Multi-site monitoring)
- ✅ Custom ping targets with add/remove functionality
- ✅ Larger settings modal for better UX
- ✅ Fix authentication for POST endpoints

### 2026-02-09 (Earlier)
- ✅ Process monitoring for server monitor widget
- ✅ Server management UI improvements
- ✅ Multi-server support in single widget
- ✅ CORS fixes for network access

---

*Last updated: 2026-02-09*
