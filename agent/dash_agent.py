#!/usr/bin/env python3
"""
Personal Dash - Server Monitoring Agent

A lightweight agent that collects system and Docker metrics from a server
and reports them to the Personal Dash backend API.

Configuration via environment variables or a .env file:
    DASH_API_URL          (required) Backend URL, e.g. https://dash.example.com/api/v1
    DASH_API_KEY          (required) Raw API key for authentication
    DASH_SERVER_ID        (required) Server ID from the dashboard
    DASH_POLL_INTERVAL    (default 60) Seconds between collection cycles
    DASH_COLLECT_DOCKER   (default true) Enable Docker container stats
    DASH_COLLECT_PROCESSES (default true) Enable process monitoring
    DASH_LOG_LEVEL        (default INFO) Logging level

Usage:
    python dash_agent.py
    python dash_agent.py --config /etc/dash-agent/agent.env
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

import psutil

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger("dash-agent")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class Config:
    api_url: str
    api_key: str
    server_id: int
    poll_interval: int = 60
    collect_docker: bool = True
    collect_processes: bool = True
    log_level: str = "INFO"


def load_env_file(path: str) -> None:
    """Parse a simple .env file and set environment variables."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                os.environ.setdefault(key, value)
    except FileNotFoundError:
        logger.error("Config file not found: %s", path)
        sys.exit(1)


def load_config(config_file: str | None = None) -> Config:
    """Load configuration from environment variables."""
    if config_file:
        load_env_file(config_file)

    api_url = os.environ.get("DASH_API_URL", "").rstrip("/")
    api_key = os.environ.get("DASH_API_KEY", "")
    server_id_str = os.environ.get("DASH_SERVER_ID", "")

    missing = []
    if not api_url:
        missing.append("DASH_API_URL")
    if not api_key:
        missing.append("DASH_API_KEY")
    if not server_id_str:
        missing.append("DASH_SERVER_ID")

    if missing:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        server_id = int(server_id_str)
    except ValueError:
        print(
            f"ERROR: DASH_SERVER_ID must be an integer, got: {server_id_str!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    poll_interval = int(os.environ.get("DASH_POLL_INTERVAL", "60"))
    collect_docker = os.environ.get("DASH_COLLECT_DOCKER", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    collect_processes = os.environ.get("DASH_COLLECT_PROCESSES", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    log_level = os.environ.get("DASH_LOG_LEVEL", "INFO").upper()

    return Config(
        api_url=api_url,
        api_key=api_key,
        server_id=server_id,
        poll_interval=max(10, poll_interval),
        collect_docker=collect_docker,
        collect_processes=collect_processes,
        log_level=log_level,
    )


def setup_logging(level: str) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ---------------------------------------------------------------------------
# System Metrics Collection
# ---------------------------------------------------------------------------


def collect_system_metrics() -> dict:
    """Collect CPU, memory, disk, and network metrics."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "disk_percent": disk.percent,
        "network_in": net.bytes_recv,
        "network_out": net.bytes_sent,
    }


# ---------------------------------------------------------------------------
# Docker Container Stats
# ---------------------------------------------------------------------------


def _calculate_cpu_percent(stats: dict) -> float:
    """Calculate container CPU % from Docker stats API response."""
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)

        if system_delta > 0 and cpu_delta >= 0:
            return round((cpu_delta / system_delta) * num_cpus * 100.0, 2)
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return 0.0


def collect_docker_stats() -> list[dict]:
    """Collect stats for all Docker containers."""
    if not DOCKER_AVAILABLE:
        return []

    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        logger.warning("Cannot connect to Docker: %s", e)
        return []

    containers = []
    for container in client.containers.list(all=True):
        info = {
            "container_id": container.short_id,
            "name": container.name,
            "image": (
                str(container.image.tags[0])
                if container.image.tags
                else str(container.image.id[:12])
            ),
            "status": container.status,
            "cpu_percent": 0.0,
            "memory_usage": 0,
            "memory_limit": 0,
        }

        if container.status == "running":
            try:
                stats = container.stats(stream=False)
                info["cpu_percent"] = _calculate_cpu_percent(stats)
                info["memory_usage"] = stats.get("memory_stats", {}).get("usage", 0)
                info["memory_limit"] = stats.get("memory_stats", {}).get("limit", 0)
            except Exception:
                pass  # Container may have stopped between list and stats

        containers.append(info)

    return containers


# ---------------------------------------------------------------------------
# Process Monitoring
# ---------------------------------------------------------------------------


def fetch_process_config(config: Config) -> list[dict]:
    """Fetch the list of processes to monitor from the backend."""
    url = f"{config.api_url}/servers/{config.server_id}/processes-config"

    req = urllib.request.Request(
        url,
        headers={"X-API-Key": config.api_key},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data
            logger.warning("Unexpected response fetching process config: %d", resp.status)
            return []
    except Exception as e:
        logger.warning("Failed to fetch process config: %s", e)
        return []


def collect_process_stats(process_configs: list[dict]) -> list[dict]:
    """Collect stats for monitored processes."""
    results = []

    for config in process_configs:
        process_name = config["process_name"]
        match_pattern = config["match_pattern"]

        is_running = False
        total_cpu = 0.0
        total_memory = 0
        found_pid = None

        try:
            # Search for matching processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    proc_name = proc.info['name'] or ""
                    cmdline = " ".join(proc.info['cmdline'] or [])

                    # Check if match pattern is in process name or command line
                    if match_pattern.lower() in proc_name.lower() or match_pattern.lower() in cmdline.lower():
                        is_running = True
                        found_pid = proc.info['pid']

                        # Get CPU percentage (one-shot)
                        cpu = proc.cpu_percent(interval=0.1)
                        total_cpu += cpu

                        # Get memory in MB
                        mem_info = proc.info.get('memory_info')
                        if mem_info:
                            total_memory += mem_info.rss // (1024 * 1024)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.warning("Error collecting stats for process %s: %s", process_name, e)

        results.append({
            "process_name": process_name,
            "match_pattern": match_pattern,
            "is_running": is_running,
            "cpu_percent": round(total_cpu, 2) if is_running else None,
            "memory_mb": total_memory if is_running else None,
            "pid": found_pid,
        })

    return results


# ---------------------------------------------------------------------------
# HTTP Sending
# ---------------------------------------------------------------------------


def send_metrics(config: Config, payload: dict) -> bool:
    """POST metrics to the dashboard backend."""
    url = f"{config.api_url}/servers/metrics/report"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": config.api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                logger.debug("Metrics sent successfully")
                return True
            logger.warning("Unexpected response: %d", resp.status)
            return False
    except urllib.error.HTTPError as e:
        if e.code == 401:
            logger.error("Authentication failed — check DASH_API_KEY")
        elif e.code == 404:
            logger.error("Server not found — check DASH_SERVER_ID")
        else:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                pass
            logger.error("HTTP error %d: %s %s", e.code, e.reason, body)
        return False
    except urllib.error.URLError as e:
        logger.warning("Connection failed: %s — will retry next cycle", e.reason)
        return False
    except Exception as e:
        logger.error("Unexpected error sending metrics: %s", e)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

shutdown_requested = False


def _handle_signal(signum: int, _frame) -> None:
    global shutdown_requested
    logger.info("Received signal %d, shutting down...", signum)
    shutdown_requested = True


def main() -> None:
    global shutdown_requested

    parser = argparse.ArgumentParser(description="Personal Dash Monitoring Agent")
    parser.add_argument("--config", help="Path to .env config file")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config.log_level)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("Dashboard Agent starting for server_id=%d", config.server_id)
    logger.info("Reporting to %s", config.api_url)
    logger.info("Poll interval: %ds", config.poll_interval)

    if config.collect_docker:
        if DOCKER_AVAILABLE:
            logger.info("Docker stats collection enabled")
        else:
            logger.warning(
                "Docker stats requested but 'docker' package not installed — skipping"
            )

    if config.collect_processes:
        logger.info("Process monitoring enabled")

    while not shutdown_requested:
        try:
            logger.debug("Collecting system metrics...")
            metrics = collect_system_metrics()
            logger.debug(
                "System: CPU=%.1f%% MEM=%.1f%% DISK=%.1f%%",
                metrics["cpu_percent"],
                metrics["memory_percent"],
                metrics["disk_percent"],
            )

            containers = []
            if config.collect_docker and DOCKER_AVAILABLE:
                logger.debug("Collecting Docker stats...")
                containers = collect_docker_stats()
                logger.debug("Docker: %d containers", len(containers))

            processes = []
            if config.collect_processes:
                logger.debug("Fetching process configuration...")
                process_configs = fetch_process_config(config)
                if process_configs:
                    logger.debug("Collecting process stats for %d processes...", len(process_configs))
                    processes = collect_process_stats(process_configs)
                    running_count = sum(1 for p in processes if p["is_running"])
                    logger.debug("Processes: %d/%d running", running_count, len(processes))

            payload = {
                "server_id": config.server_id,
                "metrics": metrics,
                "containers": containers,
                "processes": processes,
            }

            send_metrics(config, payload)

        except Exception as e:
            logger.error("Collection cycle failed: %s", e)

        # Interruptible sleep
        for _ in range(config.poll_interval):
            if shutdown_requested:
                break
            time.sleep(1)

    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
