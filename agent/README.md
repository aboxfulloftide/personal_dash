# Personal Dash - Server Monitoring Agent

A lightweight Python agent that collects system and Docker metrics from a server and reports them to the Personal Dash backend API.

## Prerequisites

- Python 3.10+
- `psutil` (required)
- `docker` Python package (optional, for Docker container stats)

## Deployment

### 1. Create a service user

```bash
sudo useradd --system --no-create-home dash-agent
# If you need Docker monitoring:
sudo usermod -aG docker dash-agent
```

### 2. Copy the agent files

```bash
sudo mkdir -p /opt/dash-agent /etc/dash-agent

# From your local machine:
scp agent/dash_agent.py yourserver:/opt/dash-agent/
scp agent/requirements.txt yourserver:/opt/dash-agent/
scp agent/dash-agent.service yourserver:/etc/systemd/system/
```

### 3. Set up Python venv and install dependencies

```bash
sudo python3 -m venv /opt/dash-agent/venv
sudo /opt/dash-agent/venv/bin/pip install -r /opt/dash-agent/requirements.txt
```

If you don't need Docker monitoring, you can skip the `docker` package:

```bash
sudo /opt/dash-agent/venv/bin/pip install psutil
```

### 4. Configure

```bash
sudo cp config.example.env /etc/dash-agent/agent.env
sudo chmod 600 /etc/dash-agent/agent.env
sudo nano /etc/dash-agent/agent.env
```

Fill in the required values:

```
DASH_API_URL=https://dash.yourdomain.com/api/v1
DASH_API_KEY=<key generated when you register this server in the dashboard>
DASH_SERVER_ID=<id from the dashboard>
DASH_POLL_INTERVAL=60
```

### 5. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dash-agent
```

### 6. Verify

```bash
sudo systemctl status dash-agent
sudo journalctl -u dash-agent -f
```

## Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DASH_API_URL` | Yes | — | Backend API URL, e.g. `https://dash.example.com/api/v1` |
| `DASH_API_KEY` | Yes | — | Raw API key (generated when registering a server) |
| `DASH_SERVER_ID` | Yes | — | Server ID assigned by the dashboard |
| `DASH_POLL_INTERVAL` | No | `60` | Seconds between metric collection cycles (minimum 10) |
| `DASH_COLLECT_DOCKER` | No | `true` | Enable Docker container stats collection |
| `DASH_LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

Configuration can also be passed via a `.env` file:

```bash
python dash_agent.py --config /path/to/agent.env
```

## Metrics Collected

### System

- CPU usage (%)
- Memory usage (%)
- Disk usage (%) — root partition
- Network bytes received (cumulative)
- Network bytes sent (cumulative)

### Docker Containers (optional)

For each container:

- Container ID, name, image, status
- CPU usage (%)
- Memory usage and limit (bytes)

## Troubleshooting

**Agent won't start — missing variables**
Check that `/etc/dash-agent/agent.env` has all required variables set.

**"Connection failed" warnings in logs**
The backend is unreachable. The agent will keep retrying each cycle. Verify `DASH_API_URL` is correct and the backend is running.

**"Authentication failed" errors**
The API key is invalid. Regenerate it from the dashboard and update `agent.env`.

**No Docker stats**
Ensure the `docker` Python package is installed and the `dash-agent` user is in the `docker` group:
```bash
sudo usermod -aG docker dash-agent
sudo systemctl restart dash-agent
```
