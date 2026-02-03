# Task 010: Server Monitoring Agent

## Objective
Build a lightweight Python monitoring agent that runs on remote servers, collects system metrics and Docker stats, and pushes data to the Personal Dash API.

## Prerequisites
- Task 009 completed (Server Monitoring Dashboard)
- API endpoint for agent metrics exists

## Agent Overview
- Standalone Python script
- Runs as systemd service
- Pushes metrics every 1 minute (configurable)
- Collects: CPU, memory, disk, network, uptime, load average
- Optionally collects Docker container stats
- Authenticates via API key

## Deliverables

### 1. Agent Directory Structure

```
agent/
├── personal_dash_agent.py    # Main agent script
├── config.yaml               # Configuration file
├── requirements.txt          # Dependencies
├── install.sh               # Installation script
└── personal-dash-agent.service  # Systemd service file
```

### 2. Agent Configuration

#### agent/config.yaml:
```yaml
# Personal Dash Monitoring Agent Configuration

# Dashboard API settings
api:
  # URL of your Personal Dash instance
  url: "http://your-dashboard-url:8000"
  # API key from dashboard (get this when adding server)
  key: "your-api-key-here"
  # API endpoint path
  endpoint: "/api/v1/servers/agent/metrics"

# Collection settings
collection:
  # Interval in seconds between metric pushes
  interval: 60
  # Collect Docker container stats (requires Docker access)
  docker_enabled: true
  # Include network stats
  network_enabled: true

# Logging
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  # Log file path (leave empty for stdout only)
  file: "/var/log/personal-dash-agent.log"
```

### 3. Main Agent Script

#### agent/personal_dash_agent.py:
```python
#!/usr/bin/env python3
"""
Personal Dash Monitoring Agent

A lightweight agent that collects system metrics and pushes them
to the Personal Dash dashboard.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

import yaml
import psutil
import requests

# Optional Docker support
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

__version__ = "1.0.0"

# Default config path
DEFAULT_CONFIG_PATH = "/etc/personal-dash-agent/config.yaml"


def setup_logging(config: dict) -> logging.Logger:
    """Configure logging based on config."""
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO").upper())
    log_file = log_config.get("file")

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        try:
            handlers.append(logging.FileHandler(log_file))
        except PermissionError:
            print(f"Warning: Cannot write to log file {log_file}")

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )

    return logging.getLogger("personal-dash-agent")


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        return yaml.safe_load(f)


def collect_cpu_metrics() -> dict:
    """Collect CPU metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "load_average": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None
    }


def collect_memory_metrics() -> dict:
    """Collect memory metrics."""
    mem = psutil.virtual_memory()
    return {
        "memory_total": round(mem.total / (1024**3), 2),  # GB
        "memory_used": round(mem.used / (1024**3), 2),    # GB
        "memory_percent": mem.percent
    }


def collect_disk_metrics() -> dict:
    """Collect disk metrics for root partition."""
    disk = psutil.disk_usage("/")
    return {
        "disk_total": round(disk.total / (1024**3), 2),  # GB
        "disk_used": round(disk.used / (1024**3), 2),    # GB
        "disk_percent": disk.percent
    }


def collect_network_metrics() -> dict:
    """Collect network I/O metrics."""
    net = psutil.net_io_counters()
    return {
        "network_bytes_sent": net.bytes_sent,
        "network_bytes_recv": net.bytes_recv
    }


def collect_uptime() -> dict:
    """Collect system uptime."""
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    return {
        "uptime_seconds": uptime_seconds
    }


def collect_docker_stats() -> list:
    """Collect Docker container statistics."""
    if not DOCKER_AVAILABLE:
        return []

    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)

        stats = []
        for container in containers:
            container_info = {
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                "status": container.status,
                "state": container.attrs.get("State", {}).get("Status", "unknown")
            }

            # Get resource stats for running containers
            if container.status == "running":
                try:
                    stats_data = container.stats(stream=False)

                    # CPU calculation
                    cpu_delta = stats_data["cpu_stats"]["cpu_usage"]["total_usage"] - \
                                stats_data["precpu_stats"]["cpu_usage"]["total_usage"]
                    system_delta = stats_data["cpu_stats"]["system_cpu_usage"] - \
                                   stats_data["precpu_stats"]["system_cpu_usage"]
                    cpu_count = stats_data["cpu_stats"].get("online_cpus", 1)

                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
                    else:
                        cpu_percent = 0.0

                    # Memory calculation
                    memory_usage = stats_data["memory_stats"].get("usage", 0)
                    memory_limit = stats_data["memory_stats"].get("limit", 1)
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0

                    # Network
                    networks = stats_data.get("networks", {})
                    network_rx = sum(n.get("rx_bytes", 0) for n in networks.values())
                    network_tx = sum(n.get("tx_bytes", 0) for n in networks.values())

                    container_info.update({
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_usage": round(memory_usage / (1024**2), 2),  # MB
                        "memory_limit": round(memory_limit / (1024**2), 2),  # MB
                        "memory_percent": round(memory_percent, 2),
                        "network_rx": network_rx,
                        "network_tx": network_tx
                    })
                except Exception as e:
                    logging.debug(f"Failed to get stats for container {container.name}: {e}")

            stats.append(container_info)

        return stats

    except docker.errors.DockerException as e:
        logging.warning(f"Docker error: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error collecting Docker stats: {e}")
        return []


def collect_all_metrics(config: dict) -> dict:
    """Collect all system metrics."""
    collection_config = config.get("collection", {})

    metrics = {}

    # Always collect core metrics
    metrics.update(collect_cpu_metrics())
    metrics.update(collect_memory_metrics())
    metrics.update(collect_disk_metrics())
    metrics.update(collect_uptime())

    # Optional network metrics
    if collection_config.get("network_enabled", True):
        metrics.update(collect_network_metrics())

    # Optional Docker metrics
    if collection_config.get("docker_enabled", True):
        containers = collect_docker_stats()
        if containers:
            metrics["containers"] = containers

    return metrics


def push_metrics(config: dict, metrics: dict, logger: logging.Logger) -> bool:
    """Push metrics to the dashboard API."""
    api_config = config.get("api", {})

    url = api_config.get("url", "").rstrip("/")
    endpoint = api_config.get("endpoint", "/api/v1/servers/agent/metrics")
    api_key = api_config.get("key")

    if not url or not api_key:
        logger.error("API URL or key not configured")
        return False

    full_url = f"{url}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.post(
            full_url,
            json=metrics,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            logger.debug("Metrics pushed successfully")
            return True
        elif response.status_code == 401:
            logger.error("Authentication failed - check API key")
            return False
        else:
            logger.warning(f"API returned status {response.status_code}: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.warning(f"Cannot connect to {url}")
        return False
    except requests.exceptions.Timeout:
        logger.warning("Request timed out")
        return False
    except Exception as e:
        logger.error(f"Error pushing metrics: {e}")
        return False


def run_agent(config: dict, logger: logging.Logger):
    """Main agent loop."""
    collection_config = config.get("collection", {})
    interval = collection_config.get("interval", 60)

    logger.info(f"Starting Personal Dash Agent v{__version__}")
    logger.info(f"Push interval: {interval} seconds")
    logger.info(f"Docker monitoring: {'enabled' if collection_config.get('docker_enabled') and DOCKER_AVAILABLE else 'disabled'}")

    consecutive_failures = 0
    max_failures = 5

    while True:
        try:
            # Collect metrics
            metrics = collect_all_metrics(config)
            logger.debug(f"Collected metrics: {json.dumps(metrics, indent=2)}")

            # Push to API
            success = push_metrics(config, metrics, logger)

            if success:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.warning(f"Failed to push metrics {consecutive_failures} times in a row")

            # Wait for next interval
            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Shutting down agent")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(interval)


def test_connection(config: dict, logger: logging.Logger):
    """Test connection to the dashboard API."""
    logger.info("Testing connection to dashboard...")

    metrics = collect_all_metrics(config)
    success = push_metrics(config, metrics, logger)

    if success:
        logger.info("✓ Connection successful!")
        logger.info(f"  Collected {len(metrics)} metric types")
        if "containers" in metrics:
            logger.info(f"  Found {len(metrics['containers'])} Docker containers")
    else:
        logger.error("✗ Connection failed")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Personal Dash Monitoring Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="Test connection and exit"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Personal Dash Agent v{__version__}"
    )

    args = parser.parse_args()

    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Create a config file at {args.config} or specify path with -c")
        sys.exit(1)

    # Setup logging
    logger = setup_logging(config)

    # Run test or main loop
    if args.test:
        test_connection(config, logger)
    else:
        run_agent(config, logger)


if __name__ == "__main__":
    main()
```

### 4. Requirements File

#### agent/requirements.txt:
```
psutil>=5.9.0
requests>=2.28.0
PyYAML>=6.0
docker>=6.0.0  # Optional, for Docker monitoring
```

### 5. Installation Script

#### agent/install.sh:
```bash
#!/bin/bash

# Personal Dash Agent Installation Script

set -e

INSTALL_DIR="/opt/personal-dash-agent"
CONFIG_DIR="/etc/personal-dash-agent"
SERVICE_NAME="personal-dash-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo_error "Please run as root (sudo ./install.sh)"
    exit 1
fi

echo_info "Installing Personal Dash Monitoring Agent..."

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [ "$(echo "$PYTHON_VERSION >= 3.8" | bc)" -eq 1 ]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo_error "Python 3.8+ is required but not found"
    exit 1
fi

echo_info "Using Python: $PYTHON_CMD ($PYTHON_VERSION)"

# Create directories
echo_info "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Copy agent files
echo_info "Copying agent files..."
cp personal_dash_agent.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/personal_dash_agent.py"

# Install Python dependencies
echo_info "Installing Python dependencies..."
$PYTHON_CMD -m pip install -r "$INSTALL_DIR/requirements.txt" --quiet

# Copy config if it doesn't exist
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo_info "Creating default config..."
    cp config.yaml "$CONFIG_DIR/"
    chmod 600 "$CONFIG_DIR/config.yaml"
    echo_warn "Edit $CONFIG_DIR/config.yaml with your API settings"
else
    echo_info "Config file already exists, skipping..."
fi

# Create systemd service
echo_info "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Personal Dash Monitoring Agent
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON_CMD $INSTALL_DIR/personal_dash_agent.py -c $CONFIG_DIR/config.yaml
Restart=always
RestartSec=10
User=root

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo_info "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit the config file:"
echo "     sudo nano $CONFIG_DIR/config.yaml"
echo ""
echo "  2. Add your dashboard URL and API key"
echo ""
echo "  3. Test the connection:"
echo "     sudo $PYTHON_CMD $INSTALL_DIR/personal_dash_agent.py -c $CONFIG_DIR/config.yaml -t"
echo ""
echo "  4. Start the service:"
echo "     sudo systemctl start $SERVICE_NAME"
echo "     sudo systemctl enable $SERVICE_NAME"
echo ""
echo "  5. Check status:"
echo "     sudo systemctl status $SERVICE_NAME"
echo ""
```

### 6. Systemd Service File

#### agent/personal-dash-agent.service:
```ini
[Unit]
Description=Personal Dash Monitoring Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/personal-dash-agent/personal_dash_agent.py -c /etc/personal-dash-agent/config.yaml
Restart=always
RestartSec=10
User=root

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=personal-dash-agent

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 7. Uninstall Script

#### agent/uninstall.sh:
```bash
#!/bin/bash

# Personal Dash Agent Uninstall Script

set -e

INSTALL_DIR="/opt/personal-dash-agent"
CONFIG_DIR="/etc/personal-dash-agent"
SERVICE_NAME="personal-dash-agent"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Please run as root"
    exit 1
fi

echo_info "Uninstalling Personal Dash Agent..."

# Stop and disable service
if systemctl is-active --quiet $SERVICE_NAME; then
    echo_info "Stopping service..."
    systemctl stop $SERVICE_NAME
fi

if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    echo_info "Disabling service..."
    systemctl disable $SERVICE_NAME
fi

# Remove service file
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo_info "Removing service file..."
    rm "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo_info "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
fi

# Ask about config
read -p "Remove configuration files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$CONFIG_DIR" ]; then
        echo_info "Removing config directory..."
        rm -rf "$CONFIG_DIR"
    fi
fi

echo_info "Uninstall complete!"
```

## Documentation

### 8. Agent README

#### agent/README.md:
```markdown
# Personal Dash Monitoring Agent

A lightweight Python agent that collects system metrics and pushes them to your Personal Dash dashboard.

## Features

- CPU, memory, disk, and network monitoring
- System uptime and load average
- Docker container stats (optional)
- Configurable push interval
- Runs as a systemd service
- Minimal resource footprint

## Requirements

- Python 3.8+
- Linux (tested on Ubuntu 20.04+, Debian 11+)
- Root access (for installation)
- Docker (optional, for container monitoring)

## Quick Install

```bash
# Download and extract agent files
# Then run:
sudo ./install.sh
```

## Manual Installation

1. Install dependencies:
```bash
pip3 install psutil requests pyyaml docker
```

2. Copy files:
```bash
sudo mkdir -p /opt/personal-dash-agent
sudo mkdir -p /etc/personal-dash-agent
sudo cp personal_dash_agent.py /opt/personal-dash-agent/
sudo cp config.yaml /etc/personal-dash-agent/
```

3. Configure:
```bash
sudo nano /etc/personal-dash-agent/config.yaml
```

4. Test:
```bash
sudo python3 /opt/personal-dash-agent/personal_dash_agent.py -t
```

5. Install service:
```bash
sudo cp personal-dash-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable personal-dash-agent
sudo systemctl start personal-dash-agent
```

## Configuration

Edit `/etc/personal-dash-agent/config.yaml`:

```yaml
api:
  url: "http://your-dashboard:8000"  # Your dashboard URL
  key: "your-api-key"                 # From dashboard server setup

collection:
  interval: 60          # Seconds between pushes
  docker_enabled: true  # Monitor Docker containers
  network_enabled: true # Collect network stats

logging:
  level: "INFO"
  file: "/var/log/personal-dash-agent.log"
```

## Commands

```bash
# Check status
sudo systemctl status personal-dash-agent

# View logs
sudo journalctl -u personal-dash-agent -f

# Restart agent
sudo systemctl restart personal-dash-agent

# Test connection
sudo python3 /opt/personal-dash-agent/personal_dash_agent.py -t
```

## Troubleshooting

### Agent not connecting
- Check API URL is accessible from server
- Verify API key is correct
- Check firewall allows outbound connections

### Docker stats not showing
- Ensure docker package is installed: `pip3 install docker`
- User must have Docker access (root or docker group)
- Check Docker daemon is running

### High CPU usage
- Increase collection interval in config
- Disable Docker monitoring if not needed

## Uninstall

```bash
sudo ./uninstall.sh
```
```

## Unit Tests

### tests/test_agent.py:
```python
import pytest
from unittest.mock import patch, MagicMock

# Import agent functions (adjust path as needed)
import sys
sys.path.insert(0, 'agent')
from personal_dash_agent import (
    collect_cpu_metrics,
    collect_memory_metrics,
    collect_disk_metrics,
    collect_uptime,
    collect_all_metrics
)

def test_collect_cpu_metrics():
    metrics = collect_cpu_metrics()
    assert "cpu_percent" in metrics
    assert isinstance(metrics["cpu_percent"], (int, float))
    assert 0 <= metrics["cpu_percent"] <= 100

def test_collect_memory_metrics():
    metrics = collect_memory_metrics()
    assert "memory_total" in metrics
    assert "memory_used" in metrics
    assert "memory_percent" in metrics
    assert metrics["memory_total"] > 0
    assert 0 <= metrics["memory_percent"] <= 100

def test_collect_disk_metrics():
    metrics = collect_disk_metrics()
    assert "disk_total" in metrics
    assert "disk_used" in metrics
    assert "disk_percent" in metrics
    assert metrics["disk_total"] > 0

def test_collect_uptime():
    metrics = collect_uptime()
    assert "uptime_seconds" in metrics
    assert metrics["uptime_seconds"] > 0

def test_collect_all_metrics():
    config = {
        "collection": {
            "docker_enabled": False,
            "network_enabled": True
        }
    }
    metrics = collect_all_metrics(config)

    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics
    assert "uptime_seconds" in metrics
    assert "network_bytes_sent" in metrics

@patch('personal_dash_agent.requests.post')
def test_push_metrics_success(mock_post):
    mock_post.return_value = MagicMock(status_code=200)

    from personal_dash_agent import push_metrics
    import logging
    logger = logging.getLogger("test")

    config = {
        "api": {
            "url": "http://localhost:8000",
            "endpoint": "/api/v1/servers/agent/metrics",
            "key": "test-key"
        }
    }

    result = push_metrics(config, {"cpu_percent": 50}, logger)
    assert result is True
    mock_post.assert_called_once()

@patch('personal_dash_agent.requests.post')
def test_push_metrics_auth_failure(mock_post):
    mock_post.return_value = MagicMock(status_code=401)

    from personal_dash_agent import push_metrics
    import logging
    logger = logging.getLogger("test")

    config = {
        "api": {
            "url": "http://localhost:8000",
            "endpoint": "/api/v1/servers/agent/metrics",
            "key": "bad-key"
        }
    }

    result = push_metrics(config, {"cpu_percent": 50}, logger)
    assert result is False
```

## Acceptance Criteria
- [ ] Agent collects CPU, memory, disk metrics
- [ ] Agent collects uptime and load average
- [ ] Agent collects network I/O stats
- [ ] Agent collects Docker container stats (when enabled)
- [ ] Agent pushes to API with correct authentication
- [ ] Agent runs as systemd service
- [ ] Install script works on fresh Linux server
- [ ] Config file is properly secured (600 permissions)
- [ ] Agent handles connection failures gracefully
- [ ] Agent logs to file and/or journal
- [ ] Test mode verifies connectivity
- [ ] Unit tests pass

## Estimated Time
3-4 hours

## Next Task
Task 011: Package Tracking Widget
