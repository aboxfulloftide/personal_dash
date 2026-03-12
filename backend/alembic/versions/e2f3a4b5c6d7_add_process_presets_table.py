"""Add process_presets table with seeded defaults

Revision ID: e2f3a4b5c6d7
Revises: d7e8f9a0b1c2
Create Date: 2026-03-11
"""
from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
branch_labels = None
depends_on = None

BUILTIN_PRESETS = [
    # (category, name, pattern, hint, sort_order)
    # Common
    ("Common", "nginx",         "nginx",            "Nginx web server / reverse proxy",                                             10),
    ("Common", "Apache",        "apache2",          "Apache HTTP server",                                                           20),
    ("Common", "PostgreSQL",    "postgres",         "PostgreSQL database server",                                                   30),
    ("Common", "MySQL",         "mysqld",           "MySQL or MariaDB database server",                                             40),
    ("Common", "Redis",         "redis-server",     "Redis in-memory data store",                                                   50),
    ("Common", "SSH daemon",    "sshd",             "OpenSSH server — confirms SSH is accessible",                                  60),
    ("Common", "Docker",        "dockerd",          "Docker container runtime daemon",                                              70),
    ("Common", "Cron",          "cron",             "System cron job scheduler",                                                    80),
    # Personal Dash
    ("Personal Dash", "Dash Backend", "personal_dash",  "FastAPI backend for this dashboard (personal-dash-backend.service)",      10),
    ("Personal Dash", "Dash Agent",   "dash_agent.py",  "Monitoring agent reporting metrics to this dashboard (dash-agent.service)", 20),
    # air_scan — server
    ("air_scan — server", "air-scan API",    "uvicorn api.main:app",  "air_scan FastAPI backend on port 8002 (air-scan-api.service)",            10),
    ("air_scan — server", "Pull scanner",    "pull_scanner.py",       "Pulls scan data from OpenWrt router every 60s (air-scan-pull.service)",   20),
    ("air_scan — server", "Device sync",     "sync_known_devices.py", "Syncs known devices from port_scan DB every 5m (air-scan-sync.service)",  30),
    ("air_scan — server", "Router watchdog", "router_watchdog.sh",    "Cron job — monitors router capture process and auto-restarts it",         40),
    # air_scan — Pi scanner
    ("air_scan — Pi scanner", "WiFi scanner", "wifi_scanner.py", "Passive WiFi beacon/probe sniffer on wlan1 in monitor mode (wifi-scanner.service)", 10),
    # air_scan — OpenWrt router
    ("air_scan — OpenWrt router", "Router capture",    "router_capture",    "iw scan + tcpdump orchestrator running on the OpenWrt router itself",          10),
    ("air_scan — OpenWrt router", "tcpdump (monitor)", "tcpdump.*wlan2mon", "Packet capture in monitor mode, spawned by router_capture.sh on the router",   20),
]


def upgrade() -> None:
    op.create_table(
        "process_presets",
        sa.Column("id",          sa.Integer(),     primary_key=True, index=True),
        sa.Column("category",    sa.String(100),   nullable=False),
        sa.Column("name",        sa.String(255),   nullable=False),
        sa.Column("pattern",     sa.String(255),   nullable=False),
        sa.Column("hint",        sa.String(500)),
        sa.Column("sort_order",  sa.Integer(),     default=0),
        sa.Column("is_builtin",  sa.Boolean(),     default=False),
        sa.Column("created_at",  sa.DateTime(),    server_default=sa.func.now()),
    )

    presets_table = sa.table(
        "process_presets",
        sa.column("category",   sa.String),
        sa.column("name",       sa.String),
        sa.column("pattern",    sa.String),
        sa.column("hint",       sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_builtin", sa.Boolean),
    )
    op.bulk_insert(presets_table, [
        {"category": cat, "name": name, "pattern": pattern, "hint": hint,
         "sort_order": sort_order, "is_builtin": True}
        for cat, name, pattern, hint, sort_order in BUILTIN_PRESETS
    ])


def downgrade() -> None:
    op.drop_table("process_presets")
