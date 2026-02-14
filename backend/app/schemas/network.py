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


class PingDataPoint(BaseModel):
    """A single data point for historical charts."""
    timestamp: datetime
    latency_ms: Optional[float]
    jitter_ms: Optional[float]
    packet_loss_pct: Optional[float]
    is_reachable: bool


class TargetHistory(BaseModel):
    """Historical data for a single target."""
    target_host: str
    target_name: Optional[str]
    data_points: list[PingDataPoint]


class PingHistoryResponse(BaseModel):
    """Response containing historical ping data for graphing."""
    targets: list[TargetHistory]
    start_time: datetime
    end_time: datetime
    total_points: int


class UptimeStat(BaseModel):
    """Uptime statistics for a single target."""
    target_host: str
    target_name: Optional[str]
    uptime_24h: float = Field(..., description="Uptime percentage for last 24 hours")
    uptime_7d: float = Field(..., description="Uptime percentage for last 7 days")
    uptime_30d: float = Field(..., description="Uptime percentage for last 30 days")
    total_checks_24h: int
    successful_checks_24h: int
    total_checks_7d: int
    successful_checks_7d: int
    total_checks_30d: int
    successful_checks_30d: int


class UptimeResponse(BaseModel):
    """Response containing uptime statistics for all targets."""
    targets: list[UptimeStat]
    calculated_at: datetime


# Speed Test Schemas

class SpeedTestRequest(BaseModel):
    """Request schema for running a speed test."""
    preferred_server_id: Optional[str] = Field(
        None,
        description="Optional server ID to use for testing"
    )


class SpeedTestResultRecord(BaseModel):
    """Schema for speed test result from database."""
    id: int
    user_id: int
    download_mbps: Optional[float]
    upload_mbps: Optional[float]
    ping_ms: Optional[float]
    server_name: Optional[str]
    server_location: Optional[str]
    server_sponsor: Optional[str]
    test_duration_seconds: Optional[float]
    timestamp: datetime
    is_successful: bool
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class SpeedTestResponse(BaseModel):
    """Response after running a speed test."""
    result: SpeedTestResultRecord
    rate_limit_reset: Optional[datetime] = Field(
        None,
        description="When the user can run another test (if rate limited)"
    )


class SpeedTestHistoryResponse(BaseModel):
    """Response containing historical speed test results."""
    tests: list[SpeedTestResultRecord]
    start_time: datetime
    end_time: datetime
    total_tests: int
    average_download_mbps: Optional[float]
    average_upload_mbps: Optional[float]


class SpeedTestStatsResponse(BaseModel):
    """Response containing speed test statistics and latest result."""
    latest_test: Optional[SpeedTestResultRecord]
    avg_download_24h: Optional[float]
    avg_upload_24h: Optional[float]
    avg_download_7d: Optional[float]
    avg_upload_7d: Optional[float]
    test_count_24h: int
    test_count_7d: int
