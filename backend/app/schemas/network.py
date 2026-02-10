from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PingTarget(BaseModel):
    """Schema for a ping target configuration."""
    host: str = Field(..., description="Hostname or IP address to ping")
    name: str = Field(..., description="Display name for the target")


class NetworkStatusRequest(BaseModel):
    """Request schema for network status check."""
    targets: list[PingTarget] = Field(
        default=[
            PingTarget(host="8.8.8.8", name="Google DNS"),
            PingTarget(host="1.1.1.1", name="Cloudflare DNS"),
            PingTarget(host="208.67.222.222", name="OpenDNS"),
        ],
        description="List of hosts to ping"
    )


class PingResultRecord(BaseModel):
    """Schema for ping result from database."""
    id: int
    target_host: str
    target_name: Optional[str]
    latency_ms: Optional[float]
    jitter_ms: Optional[float]
    packet_loss_pct: Optional[float]
    is_reachable: bool
    timestamp: datetime

    model_config = {"from_attributes": True}


class NetworkStatusRecord(BaseModel):
    """Schema for network status from database."""
    id: int
    status: str  # online, degraded, offline
    ip_address: Optional[str]
    isp: Optional[str]
    location: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


class NetworkStatusResponse(BaseModel):
    """Combined response with latest status and recent ping results."""
    status: Optional[NetworkStatusRecord]
    ping_results: list[PingResultRecord]
