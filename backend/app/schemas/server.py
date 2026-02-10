from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    """Schema for creating a new server."""
    name: str = Field(..., min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    mac_address: Optional[str] = Field(None, max_length=17)
    poll_interval: int = Field(60, ge=10, le=3600)


class ServerResponse(BaseModel):
    """Schema for server response (excludes api_key_hash)."""
    id: int
    name: str
    hostname: Optional[str]
    ip_address: Optional[str]
    mac_address: Optional[str]
    poll_interval: int
    is_online: bool
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ServerCreateResponse(BaseModel):
    """Response when creating a server - includes the raw API key (only shown once)."""
    server: ServerResponse
    api_key: str = Field(..., description="Save this key - it will not be shown again")


class ContainerInfo(BaseModel):
    """Schema for container stats from agent."""
    container_id: str
    name: Optional[str]
    image: Optional[str]
    status: Optional[str]
    cpu_percent: Optional[float]
    memory_usage: Optional[int]
    memory_limit: Optional[int]


class ProcessInfo(BaseModel):
    """Schema for process stats from agent."""
    process_name: str
    match_pattern: str
    is_running: bool
    cpu_percent: Optional[float] = None
    memory_mb: Optional[int] = None
    pid: Optional[int] = None


class MetricsData(BaseModel):
    """Schema for system metrics from agent."""
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_percent: Optional[float]
    network_in: Optional[int]
    network_out: Optional[int]


class MetricsPayload(BaseModel):
    """Schema for metrics report from agent."""
    server_id: int
    metrics: MetricsData
    containers: list[ContainerInfo] = []
    processes: list[ProcessInfo] = []


class MetricRecord(BaseModel):
    """Schema for a single metric record."""
    id: int
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_percent: Optional[float]
    network_in: Optional[int]
    network_out: Optional[int]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ContainerRecord(BaseModel):
    """Schema for container record from database."""
    id: int
    container_id: str
    name: Optional[str]
    image: Optional[str]
    status: Optional[str]
    cpu_percent: Optional[float]
    memory_usage: Optional[int]
    memory_limit: Optional[int]
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessRecord(BaseModel):
    """Schema for process record from database."""
    id: int
    process_name: str
    match_pattern: str
    is_running: bool
    cpu_percent: Optional[float]
    memory_mb: Optional[int]
    pid: Optional[int]
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessCreate(BaseModel):
    """Schema for creating a new monitored process."""
    process_name: str = Field(..., min_length=1, max_length=255)
    match_pattern: str = Field(..., min_length=1, max_length=255)


class ServerDetail(BaseModel):
    """Schema for server with recent metrics and containers."""
    server: ServerResponse
    recent_metrics: list[MetricRecord]
    containers: list[ContainerRecord]
    processes: list[ProcessRecord]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
