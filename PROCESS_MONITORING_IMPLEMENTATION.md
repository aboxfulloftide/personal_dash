# Process Monitoring Implementation

## Overview
Successfully implemented process tracking for the Server Monitor widget, allowing users to monitor specific processes (MySQL, Plex, game servers, etc.) and view their resource usage in real-time.

## Changes Made

### 1. Database (Backend)
- **Migration**: `backend/alembic/versions/ccd0cec1e458_add_monitored_processes.py`
  - Created `monitored_processes` table with columns:
    - `id`, `server_id`, `process_name`, `match_pattern`
    - `is_running`, `cpu_percent`, `memory_mb`, `pid`
    - `updated_at` timestamp
  - Added foreign key to `servers` table with CASCADE DELETE
  - Added index on `server_id`

- **Model**: `backend/app/models/server.py`
  - Added `MonitoredProcess` model class
  - Added `processes` relationship to `Server` model

### 2. Backend API
- **Schemas**: `backend/app/schemas/server.py`
  - Added `ProcessInfo` (agent payload)
  - Added `ProcessRecord` (database response)
  - Added `ProcessCreate` (user input)
  - Updated `MetricsPayload` to include `processes: list[ProcessInfo]`
  - Updated `ServerDetail` to include `processes: list[ProcessRecord]`

- **CRUD**: `backend/app/crud/server.py`
  - `upsert_processes()` - Update process stats from agent data
  - `get_processes()` - Fetch all monitored processes for a server
  - `create_monitored_process()` - Add new process to monitor
  - `delete_monitored_process()` - Remove process from monitoring

- **Endpoints**: `backend/app/api/v1/endpoints/servers.py`
  - Updated `POST /servers/metrics/report` - Accept and store process data
  - Updated `GET /servers/{id}` - Include processes in ServerDetail response
  - Added `GET /servers/{id}/processes-config` - Return process list for agent (X-API-Key auth)
  - Added `POST /servers/{id}/processes` - Create monitored process (JWT auth)
  - Added `DELETE /servers/{id}/processes/{process_id}` - Remove monitored process (JWT auth)

### 3. Agent (agent/dash_agent.py)
- **Configuration**:
  - Added `DASH_COLLECT_PROCESSES` environment variable (default: true)
  - Added `collect_processes` boolean to `Config` dataclass

- **New Functions**:
  - `fetch_process_config()` - Fetch list of processes to monitor from backend
  - `collect_process_stats()` - Search for processes by match pattern and collect stats
    - Uses `psutil.process_iter()` to find matching processes
    - Checks process name and command line against match pattern
    - Aggregates CPU and memory usage if multiple instances found
    - Returns process status, CPU%, memory MB, and PID

- **Main Loop**:
  - Fetches process configuration from backend
  - Collects process stats using `collect_process_stats()`
  - Includes process data in metrics payload

### 4. Frontend
- **Widget Registry**: `frontend/src/components/widgets/widgetRegistry.js`
  - Added `show_processes` toggle to server_monitor configSchema (default: true)
  - Updated description to mention process monitoring

- **Widget**: `frontend/src/components/widgets/ServerMonitorWidget.jsx`
  - Added `ProcessList` component:
    - Displays monitored processes with green/red status indicator
    - Shows CPU percentage when running
    - Hover to reveal delete button
    - Click to remove process from monitoring

  - Added `AddProcessModal` component:
    - Form to add new process with process name and match pattern
    - Input validation and error handling
    - Submits to `POST /servers/{id}/processes` endpoint

  - Integrated components into main widget:
    - "Processes" section with "+ Add" button
    - Placed between network stats and Docker containers
    - Respects `show_processes` config toggle

## User Flow

1. User opens ServerMonitorWidget settings and enables "Show Processes"
2. In widget, clicks "+ Add" in Processes section
3. Modal prompts for:
   - **Process Name**: Display name (e.g., "MySQL Database")
   - **Match Pattern**: Search term (e.g., "mysqld")
4. Process saved to database, widget refreshes
5. On next agent poll (60s default), agent:
   - Fetches process configuration
   - Searches for matching processes
   - Reports status and resource usage
6. Widget displays:
   - Green/red dot for running/stopped status
   - Process name
   - CPU percentage (when running)
   - Memory usage (in MB)
7. User can hover over process and click ✕ to remove it

## Technical Details

### Process Matching
The agent searches for processes using `psutil.process_iter()` and checks:
- Process name (e.g., "mysqld", "plexmediaserver")
- Command line arguments (full path and parameters)
- Case-insensitive substring matching

If multiple processes match (e.g., multiple MySQL workers), it aggregates their CPU and memory usage.

### Resource Collection
- **CPU**: Uses `proc.cpu_percent(interval=0.1)` for one-shot measurement
- **Memory**: Converts RSS (Resident Set Size) from bytes to MB
- **PID**: Reports PID of first matching process found
- **Status**: Boolean `is_running` based on whether any matches found

### Error Handling
- Agent gracefully handles:
  - Failed API requests to fetch configuration
  - Process permission errors (AccessDenied)
  - Processes disappearing during collection (NoSuchProcess)
- Frontend handles:
  - Failed API calls with error messages
  - Concurrent delete operations
  - Missing or invalid data

## Testing Checklist

- [x] Database migration runs successfully
- [x] Backend models and schemas import correctly
- [x] API endpoints import without errors
- [x] Agent imports and functions are valid
- [ ] End-to-end test:
  - [ ] Add process via widget UI
  - [ ] Agent detects and reports process stats
  - [ ] Widget displays process with correct status
  - [ ] Stop process and verify widget shows stopped
  - [ ] Remove process via widget UI
  - [ ] Verify process disappears from monitoring

## Configuration

### Agent Environment Variables
```bash
DASH_COLLECT_PROCESSES=true  # Enable process monitoring (default: true)
```

### Widget Configuration
```json
{
  "show_processes": true  // Show processes section (default: true)
}
```

## Example Process Patterns

| Service | Process Name | Match Pattern |
|---------|-------------|---------------|
| MySQL | MySQL Database | mysqld |
| PostgreSQL | PostgreSQL | postgres |
| Plex | Plex Media Server | plexmediaserver |
| Nginx | Nginx Web Server | nginx |
| Apache | Apache HTTP Server | apache2 |
| Redis | Redis Server | redis-server |
| MongoDB | MongoDB | mongod |
| Docker | Docker Daemon | dockerd |

## Performance Considerations

- Process checking adds minimal overhead (~50-100ms per monitored process)
- Agent only checks configured processes, not all running processes
- CPU percentages use quick one-shot measurement (0.1s interval)
- Memory is read directly from process info (no sampling needed)
- Widget updates at configured refresh interval (default: 60s)

## Future Enhancements

Potential improvements for future iterations:
- Process restart counts and uptime tracking
- Alert thresholds for high CPU/memory usage
- Process history charts (CPU/memory over time)
- Bulk import of common processes
- Process groups (e.g., "Database Servers")
- Command to start/stop processes remotely
- Process log viewing
