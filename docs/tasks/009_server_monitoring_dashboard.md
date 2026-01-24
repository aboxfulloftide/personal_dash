# Task 009: Server Monitoring Dashboard Integration

## Objective
Build the server monitoring dashboard UI that displays data from monitoring agents, manages server configurations, and provides Wake-on-LAN functionality.

## Prerequisites
- Task 006 completed (Widget Framework)
- Database models for servers exist

## Deliverables

### 1. Database Models

#### app/models/server.py:
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)  # For Wake-on-LAN
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="servers")
    metrics = relationship("ServerMetric", back_populates="server", cascade="all, delete-orphan")
    containers = relationship("DockerContainer", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("ServerAlert", back_populates="server", cascade="all, delete-orphan")

class ServerMetric(Base):
    __tablename__ = "server_metrics"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)

    # System metrics
    cpu_percent = Column(Float, nullable=True)
    memory_total = Column(Float, nullable=True)  # GB
    memory_used = Column(Float, nullable=True)   # GB
    memory_percent = Column(Float, nullable=True)
    disk_total = Column(Float, nullable=True)    # GB
    disk_used = Column(Float, nullable=True)     # GB
    disk_percent = Column(Float, nullable=True)

    # Network
    network_bytes_sent = Column(Float, nullable=True)
    network_bytes_recv = Column(Float, nullable=True)

    # System info
    uptime_seconds = Column(Integer, nullable=True)
    load_average = Column(JSON, nullable=True)  # [1min, 5min, 15min]

    timestamp = Column(DateTime, server_default=func.now(), index=True)

    server = relationship("Server", back_populates="metrics")

class DockerContainer(Base):
    __tablename__ = "docker_containers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    container_id = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    image = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)  # running, stopped, paused, etc.
    state = Column(String(50), nullable=True)

    # Resource usage
    cpu_percent = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)  # MB
    memory_limit = Column(Float, nullable=True)  # MB
    memory_percent = Column(Float, nullable=True)

    # Network
    network_rx = Column(Float, nullable=True)
    network_tx = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, server_default=func.now())

    server = relationship("Server", back_populates="containers")

class ServerAlert(Base):
    __tablename__ = "server_alerts"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # cpu, memory, disk, offline
    severity = Column(String(20), nullable=False)    # warning, critical
    message = Column(Text, nullable=False)
    threshold = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    server = relationship("Server", back_populates="alerts")
```

#### Update app/models/user.py:
```python
# Add to User model relationships:
servers = relationship("Server", back_populates="user", cascade="all, delete-orphan")
```

### 2. Server Management Service

#### app/services/server_service.py:
```python
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.server import Server, ServerMetric, DockerContainer, ServerAlert

def generate_api_key() -> str:
    """Generate a secure API key for server agent."""
    return secrets.token_hex(32)

async def create_server(
    db: Session,
    user_id: int,
    name: str,
    hostname: Optional[str] = None,
    ip_address: Optional[str] = None,
    mac_address: Optional[str] = None
) -> Server:
    """Create a new server entry."""
    api_key = generate_api_key()

    server = Server(
        user_id=user_id,
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        mac_address=mac_address,
        api_key=api_key
    )

    db.add(server)
    db.commit()
    db.refresh(server)
    return server

async def get_user_servers(db: Session, user_id: int) -> List[Server]:
    """Get all servers for a user."""
    return db.query(Server).filter(
        Server.user_id == user_id,
        Server.is_active == True
    ).all()

async def get_server_by_id(db: Session, server_id: int, user_id: int) -> Optional[Server]:
    """Get a specific server."""
    return db.query(Server).filter(
        Server.id == server_id,
        Server.user_id == user_id
    ).first()

async def get_server_by_api_key(db: Session, api_key: str) -> Optional[Server]:
    """Get server by API key (for agent authentication)."""
    return db.query(Server).filter(
        Server.api_key == api_key,
        Server.is_active == True
    ).first()

async def update_server(
    db: Session,
    server: Server,
    **kwargs
) -> Server:
    """Update server details."""
    for key, value in kwargs.items():
        if hasattr(server, key) and value is not None:
            setattr(server, key, value)

    db.commit()
    db.refresh(server)
    return server

async def delete_server(db: Session, server: Server) -> None:
    """Soft delete a server."""
    server.is_active = False
    db.commit()

async def regenerate_api_key(db: Session, server: Server) -> str:
    """Regenerate API key for a server."""
    new_key = generate_api_key()
    server.api_key = new_key
    db.commit()
    return new_key

async def record_metrics(
    db: Session,
    server: Server,
    metrics: dict
) -> ServerMetric:
    """Record metrics from agent."""
    server.last_seen = datetime.utcnow()

    metric = ServerMetric(
        server_id=server.id,
        cpu_percent=metrics.get("cpu_percent"),
        memory_total=metrics.get("memory_total"),
        memory_used=metrics.get("memory_used"),
        memory_percent=metrics.get("memory_percent"),
        disk_total=metrics.get("disk_total"),
        disk_used=metrics.get("disk_used"),
        disk_percent=metrics.get("disk_percent"),
        network_bytes_sent=metrics.get("network_bytes_sent"),
        network_bytes_recv=metrics.get("network_bytes_recv"),
        uptime_seconds=metrics.get("uptime_seconds"),
        load_average=metrics.get("load_average")
    )

    db.add(metric)
    db.commit()

    # Check for alerts
    await check_alerts(db, server, metrics)

    return metric

async def get_latest_metrics(db: Session, server_id: int) -> Optional[ServerMetric]:
    """Get most recent metrics for a server."""
    return db.query(ServerMetric).filter(
        ServerMetric.server_id == server_id
    ).order_by(desc(ServerMetric.timestamp)).first()

async def get_metrics_history(
    db: Session,
    server_id: int,
    hours: int = 24
) -> List[ServerMetric]:
    """Get metrics history for a server."""
    since = datetime.utcnow() - timedelta(hours=hours)
    return db.query(ServerMetric).filter(
        ServerMetric.server_id == server_id,
        ServerMetric.timestamp >= since
    ).order_by(ServerMetric.timestamp).all()

async def update_containers(
    db: Session,
    server: Server,
    containers: List[dict]
) -> None:
    """Update Docker container info."""
    # Get existing containers
    existing = {c.container_id: c for c in server.containers}

    seen_ids = set()
    for container_data in containers:
        container_id = container_data.get("id")
        seen_ids.add(container_id)

        if container_id in existing:
            # Update existing
            container = existing[container_id]
            container.name = container_data.get("name", container.name)
            container.image = container_data.get("image")
            container.status = container_data.get("status")
            container.state = container_data.get("state")
            container.cpu_percent = container_data.get("cpu_percent")
            container.memory_usage = container_data.get("memory_usage")
            container.memory_limit = container_data.get("memory_limit")
            container.memory_percent = container_data.get("memory_percent")
            container.network_rx = container_data.get("network_rx")
            container.network_tx = container_data.get("network_tx")
            container.last_updated = datetime.utcnow()
        else:
            # Create new
            container = DockerContainer(
                server_id=server.id,
                container_id=container_id,
                name=container_data.get("name", "unknown"),
                image=container_data.get("image"),
                status=container_data.get("status"),
                state=container_data.get("state"),
                cpu_percent=container_data.get("cpu_percent"),
                memory_usage=container_data.get("memory_usage"),
                memory_limit=container_data.get("memory_limit"),
                memory_percent=container_data.get("memory_percent"),
                network_rx=container_data.get("network_rx"),
                network_tx=container_data.get("network_tx")
            )
            db.add(container)

    # Remove containers that no longer exist
    for container_id, container in existing.items():
        if container_id not in seen_ids:
            db.delete(container)

    db.commit()

async def check_alerts(db: Session, server: Server, metrics: dict) -> None:
    """Check metrics against thresholds and create alerts."""
    # Default thresholds (could be configurable per server)
    thresholds = {
        "cpu": {"warning": 80, "critical": 95},
        "memory": {"warning": 80, "critical": 95},
        "disk": {"warning": 85, "critical": 95}
    }

    alerts_to_create = []

    # CPU check
    cpu = metrics.get("cpu_percent")
    if cpu:
        if cpu >= thresholds["cpu"]["critical"]:
            alerts_to_create.append(("cpu", "critical", f"CPU usage critical: {cpu:.1f}%", thresholds["cpu"]["critical"], cpu))
        elif cpu >= thresholds["cpu"]["warning"]:
            alerts_to_create.append(("cpu", "warning", f"CPU usage high: {cpu:.1f}%", thresholds["cpu"]["warning"], cpu))

    # Memory check
    mem = metrics.get("memory_percent")
    if mem:
        if mem >= thresholds["memory"]["critical"]:
            alerts_to_create.append(("memory", "critical", f"Memory usage critical: {mem:.1f}%", thresholds["memory"]["critical"], mem))
        elif mem >= thresholds["memory"]["warning"]:
            alerts_to_create.append(("memory", "warning", f"Memory usage high: {mem:.1f}%", thresholds["memory"]["warning"], mem))

    # Disk check
    disk = metrics.get("disk_percent")
    if disk:
        if disk >= thresholds["disk"]["critical"]:
            alerts_to_create.append(("disk", "critical", f"Disk usage critical: {disk:.1f}%", thresholds["disk"]["critical"], disk))
        elif disk >= thresholds["disk"]["warning"]:
            alerts_to_create.append(("disk", "warning", f"Disk usage high: {disk:.1f}%", thresholds["disk"]["warning"], disk))

    for alert_type, severity, message, threshold, value in alerts_to_create:
        # Check if similar unresolved alert exists
        existing = db.query(ServerAlert).filter(
            ServerAlert.server_id == server.id,
            ServerAlert.alert_type == alert_type,
            ServerAlert.is_resolved == False
        ).first()

        if not existing:
            alert = ServerAlert(
                server_id=server.id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                threshold=threshold,
                current_value=value
            )
            db.add(alert)

    db.commit()

async def get_active_alerts(db: Session, user_id: int) -> List[ServerAlert]:
    """Get all active alerts for user's servers."""
    return db.query(ServerAlert).join(Server).filter(
        Server.user_id == user_id,
        ServerAlert.is_resolved == False
    ).order_by(desc(ServerAlert.created_at)).all()

async def resolve_alert(db: Session, alert_id: int) -> None:
    """Mark an alert as resolved."""
    alert = db.query(ServerAlert).filter(ServerAlert.id == alert_id).first()
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.commit()
```

### 3. Wake-on-LAN Service

#### app/services/wol_service.py:
```python
import socket
import struct
from typing import Optional

def create_magic_packet(mac_address: str) -> bytes:
    """Create a Wake-on-LAN magic packet."""
    # Remove separators and convert to bytes
    mac_address = mac_address.replace(":", "").replace("-", "")
    if len(mac_address) != 12:
        raise ValueError("Invalid MAC address format")

    mac_bytes = bytes.fromhex(mac_address)

    # Magic packet: 6 bytes of 0xFF followed by MAC address repeated 16 times
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    return magic_packet

async def send_wol(mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> bool:
    """Send Wake-on-LAN packet."""
    try:
        magic_packet = create_magic_packet(mac_address)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, port))
        sock.close()

        return True
    except Exception as e:
        print(f"Wake-on-LAN failed: {e}")
        return False
```

### 4. Server API Endpoints

#### app/api/v1/endpoints/servers.py:
```python
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import server_service
from app.services.wol_service import send_wol

router = APIRouter(prefix="/servers", tags=["Server Monitoring"])

# Schemas
class ServerCreate(BaseModel):
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None

class ServerResponse(BaseModel):
    id: int
    name: str
    hostname: Optional[str]
    ip_address: Optional[str]
    mac_address: Optional[str]
    last_seen: Optional[datetime]
    is_online: bool

    class Config:
        from_attributes = True

class ServerWithKey(ServerResponse):
    api_key: str

class MetricsPayload(BaseModel):
    cpu_percent: Optional[float] = None
    memory_total: Optional[float] = None
    memory_used: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_total: Optional[float] = None
    disk_used: Optional[float] = None
    disk_percent: Optional[float] = None
    network_bytes_sent: Optional[float] = None
    network_bytes_recv: Optional[float] = None
    uptime_seconds: Optional[int] = None
    load_average: Optional[List[float]] = None
    containers: Optional[List[dict]] = None

# User endpoints
@router.get("", response_model=List[ServerResponse])
async def list_servers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all servers for current user."""
    servers = await server_service.get_user_servers(db, current_user.id)

    # Add online status
    from datetime import timedelta
    now = datetime.utcnow()
    results = []
    for server in servers:
        is_online = server.last_seen and (now - server.last_seen) < timedelta(minutes=2)
        results.append({
            **server.__dict__,
            "is_online": is_online
        })

    return results

@router.post("", response_model=ServerWithKey)
async def create_server(
    data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new server."""
    server = await server_service.create_server(
        db,
        user_id=current_user.id,
        name=data.name,
        hostname=data.hostname,
        ip_address=data.ip_address,
        mac_address=data.mac_address
    )
    return {**server.__dict__, "is_online": False}

@router.get("/{server_id}")
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get server details with latest metrics."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    metrics = await server_service.get_latest_metrics(db, server_id)

    from datetime import timedelta
    now = datetime.utcnow()
    is_online = server.last_seen and (now - server.last_seen) < timedelta(minutes=2)

    return {
        "server": {**server.__dict__, "is_online": is_online},
        "metrics": metrics.__dict__ if metrics else None,
        "containers": [c.__dict__ for c in server.containers]
    }

@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update server details."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server = await server_service.update_server(db, server, **data.dict(exclude_unset=True))

    from datetime import timedelta
    now = datetime.utcnow()
    is_online = server.last_seen and (now - server.last_seen) < timedelta(minutes=2)

    return {**server.__dict__, "is_online": is_online}

@router.delete("/{server_id}")
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a server."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    await server_service.delete_server(db, server)
    return {"message": "Server deleted"}

@router.post("/{server_id}/regenerate-key")
async def regenerate_key(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate API key for a server."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    new_key = await server_service.regenerate_api_key(db, server)
    return {"api_key": new_key}

@router.get("/{server_id}/metrics")
async def get_metrics_history(
    server_id: int,
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics history for a server."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    metrics = await server_service.get_metrics_history(db, server_id, hours)
    return {"metrics": [m.__dict__ for m in metrics]}

@router.post("/{server_id}/wake")
async def wake_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send Wake-on-LAN packet to server."""
    server = await server_service.get_server_by_id(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not server.mac_address:
        raise HTTPException(status_code=400, detail="MAC address not configured")

    success = await send_wol(server.mac_address)
    if success:
        return {"message": "Wake-on-LAN packet sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Wake-on-LAN packet")

@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active alerts."""
    alerts = await server_service.get_active_alerts(db, current_user.id)
    return {"alerts": [a.__dict__ for a in alerts]}

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve an alert."""
    await server_service.resolve_alert(db, alert_id)
    return {"message": "Alert resolved"}

# Agent endpoint (authenticated via API key)
@router.post("/agent/metrics")
async def submit_metrics(
    data: MetricsPayload,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    """Submit metrics from monitoring agent."""
    server = await server_service.get_server_by_api_key(db, x_api_key)
    if not server:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Record metrics
    await server_service.record_metrics(db, server, data.dict())

    # Update containers if provided
    if data.containers:
        await server_service.update_containers(db, server, data.containers)

    return {"status": "ok"}
```

#### Update app/api/v1/router.py:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, weather, widgets, stocks, crypto, servers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weather.router)
api_router.include_router(widgets.router)
api_router.include_router(stocks.router)
api_router.include_router(crypto.router)
api_router.include_router(servers.router)
```

### 5. Frontend Server Monitoring Widget

#### src/components/widgets/ServerMonitorWidget.jsx:
```jsx
import { useState, useEffect } from 'react';
import api from '../../services/api';

export default function ServerMonitorWidget({ config }) {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverDetails, setServerDetails] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddServer, setShowAddServer] = useState(false);

  useEffect(() => {
    fetchServers();
    fetchAlerts();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchServers();
      if (selectedServer) {
        fetchServerDetails(selectedServer);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedServer) {
      fetchServerDetails(selectedServer);
    }
  }, [selectedServer]);

  const fetchServers = async () => {
    try {
      const response = await api.get('/servers');
      setServers(response.data);
      if (response.data.length > 0 && !selectedServer) {
        setSelectedServer(response.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch servers:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchServerDetails = async (serverId) => {
    try {
      const response = await api.get(`/servers/${serverId}`);
      setServerDetails(response.data);
    } catch (err) {
      console.error('Failed to fetch server details:', err);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await api.get('/servers/alerts/active');
      setAlerts(response.data.alerts);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  };

  const handleWakeServer = async (serverId) => {
    try {
      await api.post(`/servers/${serverId}/wake`);
      alert('Wake-on-LAN packet sent!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to send WoL packet');
    }
  };

  const formatUptime = (seconds) => {
    if (!seconds) return '-';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '-';
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (servers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <span className="text-4xl mb-3">🖥️</span>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          No servers configured
        </p>
        <button
          onClick={() => setShowAddServer(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
        >
          Add Server
        </button>
      </div>
    );
  }

  const metrics = serverDetails?.metrics;
  const containers = serverDetails?.containers || [];

  return (
    <div className="h-full flex flex-col">
      {/* Alerts Banner */}
      {alerts.length > 0 && (
        <div className="mb-2 p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400 text-xs">
            <span>⚠️</span>
            <span>{alerts.length} active alert{alerts.length > 1 ? 's' : ''}</span>
          </div>
        </div>
      )}

      {/* Server Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 mb-2">
        {servers.map((server) => (
          <button
            key={server.id}
            onClick={() => setSelectedServer(server.id)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              selectedServer === server.id
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${
              server.is_online ? 'bg-green-500' : 'bg-gray-400'
            }`}></span>
            {server.name}
          </button>
        ))}
        <button
          onClick={() => setShowAddServer(true)}
          className="flex-shrink-0 px-2 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          +
        </button>
      </div>

      {/* Server Details */}
      {serverDetails && (
        <div className="flex-1 overflow-y-auto">
          {/* Status Header */}
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {serverDetails.server.name}
              </h3>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {serverDetails.server.hostname || serverDetails.server.ip_address || 'No address'}
              </span>
            </div>
            <div className="flex gap-2">
              {serverDetails.server.mac_address && !serverDetails.server.is_online && (
                <button
                  onClick={() => handleWakeServer(serverDetails.server.id)}
                  className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-900/50"
                >
                  Wake
                </button>
              )}
            </div>
          </div>

          {/* Metrics Grid */}
          {metrics ? (
            <div className="grid grid-cols-2 gap-2 mb-3">
              <MetricCard
                label="CPU"
                value={`${metrics.cpu_percent?.toFixed(1)}%`}
                percent={metrics.cpu_percent}
              />
              <MetricCard
                label="Memory"
                value={`${metrics.memory_percent?.toFixed(1)}%`}
                subtext={`${metrics.memory_used?.toFixed(1)} / ${metrics.memory_total?.toFixed(1)} GB`}
                percent={metrics.memory_percent}
              />
              <MetricCard
                label="Disk"
                value={`${metrics.disk_percent?.toFixed(1)}%`}
                subtext={`${metrics.disk_used?.toFixed(0)} / ${metrics.disk_total?.toFixed(0)} GB`}
                percent={metrics.disk_percent}
              />
              <MetricCard
                label="Uptime"
                value={formatUptime(metrics.uptime_seconds)}
              />
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
              {serverDetails.server.is_online ? 'Loading metrics...' : 'Server offline'}
            </div>
          )}

          {/* Docker Containers */}
          {containers.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                Docker Containers ({containers.length})
              </h4>
              <div className="space-y-1">
                {containers.slice(0, 5).map((container) => (
                  <div
                    key={container.container_id}
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        container.status === 'running' ? 'bg-green-500' : 'bg-gray-400'
                      }`}></span>
                      <span className="font-medium text-gray-900 dark:text-white truncate max-w-[100px]">
                        {container.name}
                      </span>
                    </div>
                    <div className="text-gray-500 dark:text-gray-400">
                      {container.cpu_percent?.toFixed(1)}% / {container.memory_usage?.toFixed(0)}MB
                    </div>
                  </div>
                ))}
                {containers.length > 5 && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    +{containers.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add Server Modal */}
      {showAddServer && (
        <AddServerModal
          onClose={() => setShowAddServer(false)}
          onAdd={() => {
            setShowAddServer(false);
            fetchServers();
          }}
        />
      )}
    </div>
  );
}

function MetricCard({ label, value, subtext, percent }) {
  const getColor = (p) => {
    if (!p) return 'bg-gray-200 dark:bg-gray-600';
    if (p >= 90) return 'bg-red-500';
    if (p >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-semibold text-gray-900 dark:text-white">{value || '-'}</div>
      {subtext && (
        <div className="text-xs text-gray-500 dark:text-gray-400">{subtext}</div>
      )}
      {percent !== undefined && (
        <div className="mt-1 h-1 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
          <div
            className={`h-full ${getColor(percent)} transition-all`}
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}

function AddServerModal({ onClose, onAdd }) {
  const [name, setName] = useState('');
  const [hostname, setHostname] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [macAddress, setMacAddress] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setLoading(true);
      const response = await api.post('/servers', {
        name: name.trim(),
        hostname: hostname.trim() || null,
        ip_address: ipAddress.trim() || null,
        mac_address: macAddress.trim() || null
      });
      setApiKey(response.data.api_key);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg p-4 w-96 max-w-[90vw]">
        {!apiKey ? (
          <>
            <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">Add Server</h3>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Server Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="My Server"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Hostname
                </label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="server.local"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  IP Address
                </label>
                <input
                  type="text"
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="192.168.1.100"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                  MAC Address (for Wake-on-LAN)
                </label>
                <input
                  type="text"
                  value={macAddress}
                  onChange={(e) => setMacAddress(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="AA:BB:CC:DD:EE:FF"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-3 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !name.trim()}
                  className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <>
            <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">Server Created!</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Use this API key in your monitoring agent:
            </p>
            <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-md font-mono text-xs break-all mb-4">
              {apiKey}
            </div>
            <p className="text-xs text-yellow-600 dark:text-yellow-400 mb-4">
              ⚠️ Save this key now! It won't be shown again.
            </p>
            <button
              onClick={onAdd}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
            >
              Done
            </button>
          </>
        )}
      </div>
    </div>
  );
}
```

### 6. Update Widget Registry

#### Update src/components/widgets/widgetRegistry.js:
```javascript
const widgetRegistry = {
  // ... existing widgets ...
  serverMonitor: {
    component: () => import('./ServerMonitorWidget'),
    name: 'Server Monitor',
    description: 'Monitor servers and Docker containers',
    defaultSize: { w: 4, h: 4 },
    minSize: { w: 3, h: 3 },
    maxSize: { w: 6, h: 6 }
  }
};
```

## Unit Tests

### tests/test_servers.py:
```python
import pytest
from app.services.server_service import (
    create_server,
    get_user_servers,
    get_server_by_api_key,
    record_metrics,
    generate_api_key
)
from app.services.wol_service import create_magic_packet

def test_generate_api_key():
    key = generate_api_key()
    assert len(key) == 64
    assert key.isalnum()

def test_create_magic_packet():
    mac = "AA:BB:CC:DD:EE:FF"
    packet = create_magic_packet(mac)
    assert len(packet) == 102  # 6 + 16*6
    assert packet[:6] == b'\xff' * 6

def test_create_magic_packet_invalid():
    with pytest.raises(ValueError):
        create_magic_packet("invalid")

@pytest.mark.asyncio
async def test_create_server(db_session, test_user):
    server = await create_server(
        db_session,
        user_id=test_user.id,
        name="Test Server",
        hostname="test.local"
    )
    assert server.name == "Test Server"
    assert server.api_key is not None
    assert len(server.api_key) == 64

@pytest.mark.asyncio
async def test_get_server_by_api_key(db_session, test_user):
    server = await create_server(
        db_session,
        user_id=test_user.id,
        name="Test Server"
    )

    found = await get_server_by_api_key(db_session, server.api_key)
    assert found is not None
    assert found.id == server.id

@pytest.mark.asyncio
async def test_record_metrics(db_session, test_user):
    server = await create_server(
        db_session,
        user_id=test_user.id,
        name="Test Server"
    )

    metrics = {
        "cpu_percent": 45.5,
        "memory_percent": 60.0,
        "disk_percent": 70.0
    }

    metric = await record_metrics(db_session, server, metrics)
    assert metric.cpu_percent == 45.5
    assert metric.memory_percent == 60.0
```

## Acceptance Criteria
- [ ] Can add/edit/delete servers
- [ ] API key generated on server creation
- [ ] Server list shows online/offline status
- [ ] Metrics display (CPU, memory, disk, uptime)
- [ ] Docker containers list displays
- [ ] Wake-on-LAN button works (when MAC configured)
- [ ] Alerts display for high resource usage
- [ ] Agent endpoint accepts metrics with API key auth
- [ ] Data refreshes automatically
- [ ] Unit tests pass

## Estimated Time
4-5 hours

## Next Task
Task 010: Server Monitoring Agent
