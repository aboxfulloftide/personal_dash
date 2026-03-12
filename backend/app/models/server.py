from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255))
    ip_address = Column(String(45))
    mac_address = Column(String(17))
    api_key_hash = Column(String(255), nullable=False)
    poll_interval = Column(Integer, default=60)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="servers")
    metrics = relationship("ServerMetric", back_populates="server", cascade="all, delete-orphan")
    containers = relationship("DockerContainer", back_populates="server", cascade="all, delete-orphan")
    processes = relationship("MonitoredProcess", back_populates="server", cascade="all, delete-orphan")
    drives = relationship("MonitoredDrive", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("ServerAlert", back_populates="server", cascade="all, delete-orphan")


class ServerMetric(Base):
    __tablename__ = "server_metrics"

    id = Column(BigInteger, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    network_in = Column(BigInteger)
    network_out = Column(BigInteger)
    temperatures_json = Column(Text)  # JSON: {"CPU": 52.5, "GPU": 45.0, ...}
    recorded_at = Column(DateTime, server_default=func.now(), index=True)

    server = relationship("Server", back_populates="metrics")


class DockerContainer(Base):
    __tablename__ = "docker_containers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    container_id = Column(String(64), nullable=False)
    name = Column(String(255))
    image = Column(String(255))
    status = Column(String(50))
    cpu_percent = Column(Float)
    memory_usage = Column(BigInteger)
    memory_limit = Column(BigInteger)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    server = relationship("Server", back_populates="containers")


class MonitoredProcess(Base):
    __tablename__ = "monitored_processes"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    process_name = Column(String(255), nullable=False)
    match_pattern = Column(String(255), nullable=False)
    is_running = Column(Boolean, default=False)
    cpu_percent = Column(Float)
    memory_mb = Column(BigInteger)
    pid = Column(Integer)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    server = relationship("Server", back_populates="processes")


class MonitoredDrive(Base):
    __tablename__ = "monitored_drives"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    mount_point = Column(String(255), nullable=False)
    device = Column(String(255))
    fstype = Column(String(50))
    total_bytes = Column(BigInteger)
    used_bytes = Column(BigInteger)
    free_bytes = Column(BigInteger)
    percent_used = Column(Float)
    is_mounted = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    server = relationship("Server", back_populates="drives")


class ServerAlert(Base):
    __tablename__ = "server_alerts"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    threshold = Column(Float)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    server = relationship("Server", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(BigInteger, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("server_alerts.id", ondelete="CASCADE"), nullable=False)
    triggered_value = Column(Float)
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    triggered_at = Column(DateTime, server_default=func.now())

    alert = relationship("ServerAlert", back_populates="history")


class ProcessPreset(Base):
    __tablename__ = "process_presets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    pattern = Column(String(255), nullable=False)
    hint = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_builtin = Column(Boolean, default=False)  # True = seeded default, False = user-added
    created_at = Column(DateTime, server_default=func.now())
