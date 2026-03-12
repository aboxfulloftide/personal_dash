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


class DriveInfo(BaseModel):
    """Schema for drive stats from agent."""
    mount_point: str
    device: Optional[str] = None
    fstype: Optional[str] = None
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    percent_used: Optional[float] = None
    is_mounted: bool
    is_readonly: bool = False


class MetricsData(BaseModel):
    """Schema for system metrics from agent."""
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_percent: Optional[float]
    network_in: Optional[int]
    network_out: Optional[int]
    temperatures: Optional[dict[str, float]] = None  # {"CPU": 52.5, "GPU": 45.0}


class MetricsPayload(BaseModel):
    """Schema for metrics report from agent."""
    server_id: int
    metrics: MetricsData
    containers: list[ContainerInfo] = []
    processes: list[ProcessInfo] = []
    drives: list[DriveInfo] = []


class MetricRecord(BaseModel):
    """Schema for a single metric record."""
    id: int
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_percent: Optional[float]
    network_in: Optional[int]
    network_out: Optional[int]
    temperatures: Optional[dict[str, float]] = None
    recorded_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Deserialize temperatures_json when loading from DB."""
        import json as _json
        data = super().model_validate(obj, **kwargs)
        # If temperatures is None but temperatures_json exists on the ORM object, parse it
        if data.temperatures is None and hasattr(obj, 'temperatures_json') and obj.temperatures_json:
            try:
                data.temperatures = _json.loads(obj.temperatures_json)
            except Exception:
                pass
        return data


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


class DriveRecord(BaseModel):
    """Schema for drive record from database."""
    id: int
    mount_point: str
    device: Optional[str]
    fstype: Optional[str]
    total_bytes: Optional[int]
    used_bytes: Optional[int]
    free_bytes: Optional[int]
    percent_used: Optional[float]
    is_mounted: bool
    is_readonly: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class DriveCreate(BaseModel):
    """Schema for creating a new monitored drive."""
    mount_point: str = Field(..., min_length=1, max_length=255, pattern="^/.*")


class ServerDetail(BaseModel):
    """Schema for server with recent metrics and containers."""
    server: ServerResponse
    recent_metrics: list[MetricRecord]
    containers: list[ContainerRecord]
    processes: list[ProcessRecord]
    drives: list[DriveRecord]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ProcessPresetCreate(BaseModel):
    """Schema for creating a process preset."""
    category: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    pattern: str = Field(..., min_length=1, max_length=255)
    hint: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(0)


class ProcessPresetResponse(BaseModel):
    """Schema for a process preset response."""
    id: int
    category: str
    name: str
    pattern: str
    hint: Optional[str]
    sort_order: int
    is_builtin: bool

    model_config = {"from_attributes": True}


class DeployRequest(BaseModel):
    """Schema for SSH deployment request."""
    ssh_host: str
    ssh_port: int = Field(22, ge=1, le=65535)
    ssh_user: str = "root"
    ssh_password: Optional[str] = None
    ssh_key: Optional[str] = None  # PEM-encoded private key text
    sudo_password: Optional[str] = None  # Defaults to ssh_password if not set
    backend_url: Optional[str] = None  # Full URL for DASH_API_URL, e.g. http://192.168.1.10:8000/api/v1
    install_dir: str = "/opt/dash-agent"
    env_dir: str = "/etc/dash-agent"
    service_name: str = "dash-agent"


class DeployResponse(BaseModel):
    """Schema for SSH deployment response."""
    success: bool
    log: list[str]
