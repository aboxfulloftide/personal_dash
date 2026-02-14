import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, get_db
from app.crud import network as network_crud
from app.crud import speedtest as speedtest_crud
from app.schemas.network import (
    NetworkStatusRequest,
    NetworkStatusResponse,
    PingHistoryResponse,
    UptimeResponse,
    TargetHistory,
    PingDataPoint,
    UptimeStat,
    SpeedTestRequest,
    SpeedTestResponse,
    SpeedTestHistoryResponse,
    SpeedTestStatsResponse,
)
from app.utils.network_utils import (
    ping_host,
    get_public_ip_info,
    determine_connection_status,
)

router = APIRouter(prefix="/network", tags=["Network"])


@router.post("/status", response_model=NetworkStatusResponse)
async def get_network_status(
    request: NetworkStatusRequest,
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Run network diagnostics and return connection status.

    This endpoint:
    1. Pings multiple target hosts (configurable, defaults to Google DNS, Cloudflare, OpenDNS)
    2. Determines overall connection status (online/degraded/offline)
    3. Fetches public IP address and ISP information
    4. Stores results in database for historical tracking
    5. Returns current status and ping results
    """
    user_id = current_user.id
    targets = request.targets

    # Run ping tests in parallel for all targets
    ping_tasks = [
        asyncio.to_thread(ping_host, target.host)
        for target in targets
    ]
    ping_results = await asyncio.gather(*ping_tasks)

    # Combine results with target information
    ping_data = []
    for i, target in enumerate(targets):
        result = ping_results[i]
        ping_data.append({
            "target_host": target.host,
            "target_name": target.name,
            **result,
        })

    # Determine overall connection status
    connection_status = determine_connection_status(ping_results)

    # Get public IP and ISP info
    ip_info = await get_public_ip_info()

    # Store network status in database
    network_status = network_crud.create_network_status(
        db=db,
        user_id=user_id,
        status=connection_status,
        ip_address=ip_info["ip_address"],
        isp=ip_info["isp"],
        location=ip_info["location"],
    )

    # Store ping results in database
    ping_records = []
    for data in ping_data:
        ping_record = network_crud.create_ping_result(
            db=db,
            user_id=user_id,
            target_host=data["target_host"],
            target_name=data["target_name"],
            latency_ms=data["latency_ms"],
            jitter_ms=data["jitter_ms"],
            packet_loss_pct=data["packet_loss_pct"],
            is_reachable=data["is_reachable"],
        )
        ping_records.append(ping_record)

    return NetworkStatusResponse(
        status=network_status,
        ping_results=ping_records,
    )


@router.get("/ping-history", response_model=PingHistoryResponse)
async def get_ping_history(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history to retrieve"),
    target_host: str | None = Query(default=None, description="Filter by specific target host"),
):
    """
    Get historical ping results for graphing.

    Returns time-series data points for all targets (or a specific target) within the specified time range.
    For periods >7 days (168 hours), data may be aggregated to reduce response size.
    """
    user_id = current_user.id

    # Get historical data grouped by target
    history_by_target = network_crud.get_ping_history(
        db=db,
        user_id=user_id,
        hours=hours,
        target_host=target_host,
    )

    # Convert to response schema
    targets = []
    total_points = 0
    start_time = None
    end_time = None

    for target_host, ping_results in history_by_target.items():
        if not ping_results:
            continue

        # Convert ping results to data points
        data_points = [
            PingDataPoint(
                timestamp=result.timestamp,
                latency_ms=result.latency_ms,
                jitter_ms=result.jitter_ms,
                packet_loss_pct=result.packet_loss_pct,
                is_reachable=result.is_reachable,
            )
            for result in ping_results
        ]

        total_points += len(data_points)

        # Track time range
        if data_points:
            if start_time is None or data_points[0].timestamp < start_time:
                start_time = data_points[0].timestamp
            if end_time is None or data_points[-1].timestamp > end_time:
                end_time = data_points[-1].timestamp

        targets.append(
            TargetHistory(
                target_host=target_host,
                target_name=ping_results[0].target_name if ping_results else None,
                data_points=data_points,
            )
        )

    # Default to current time if no data
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if start_time is None:
        start_time = now
    if end_time is None:
        end_time = now

    return PingHistoryResponse(
        targets=targets,
        start_time=start_time,
        end_time=end_time,
        total_points=total_points,
    )


@router.get("/uptime", response_model=UptimeResponse)
async def get_uptime_stats(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Calculate uptime statistics for all monitored targets.

    Returns uptime percentages for 24h, 7d, and 30d windows, along with check counts.
    Uptime is calculated as the percentage of successful pings (is_reachable=True).
    """
    user_id = current_user.id

    # Get uptime stats for all targets
    stats_by_target = network_crud.calculate_uptime_stats(db=db, user_id=user_id)

    # Convert to response schema
    targets = []
    for target_host, stats in stats_by_target.items():
        targets.append(
            UptimeStat(
                target_host=target_host,
                target_name=stats.get("target_name"),
                uptime_24h=stats["uptime_24h"],
                uptime_7d=stats["uptime_7d"],
                uptime_30d=stats["uptime_30d"],
                total_checks_24h=stats["total_checks_24h"],
                successful_checks_24h=stats["successful_checks_24h"],
                total_checks_7d=stats["total_checks_7d"],
                successful_checks_7d=stats["successful_checks_7d"],
                total_checks_30d=stats["total_checks_30d"],
                successful_checks_30d=stats["successful_checks_30d"],
            )
        )

    return UptimeResponse(
        targets=targets,
        calculated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


# Speed Test Endpoints

@router.post("/speed-test", response_model=SpeedTestResponse, status_code=200)
async def run_speed_test(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    request: SpeedTestRequest = Body(default=SpeedTestRequest()),
):
    """
    Run a network speed test to measure download/upload bandwidth.

    This endpoint:
    1. Checks rate limiting (15 min minimum between tests)
    2. Runs speedtest-cli to measure download and upload speeds
    3. Stores results in database for historical tracking
    4. Returns test results with rate limit information

    Rate limiting: Tests are limited to once per 15 minutes per user.
    Test duration: Typically 30-60 seconds.
    """
    from app.utils.speedtest_utils import run_speedtest
    from fastapi import HTTPException

    user_id = current_user.id

    # Check rate limiting
    is_rate_limited, reset_time = speedtest_crud.check_rate_limit(
        db=db,
        user_id=user_id,
        min_interval_seconds=900,  # 15 minutes
    )

    if is_rate_limited:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded. Please wait before running another speed test.",
                "rate_limit_reset": reset_time.isoformat() if reset_time else None,
            }
        )

    # Run speed test (blocking operation, run in thread pool)
    test_result = await asyncio.to_thread(
        run_speedtest,
        preferred_server_id=request.preferred_server_id,
    )

    # Store result in database
    speed_test_record = speedtest_crud.create_speed_test_result(
        db=db,
        user_id=user_id,
        **test_result,
    )

    # Calculate next allowed test time
    next_test_time = speed_test_record.timestamp.replace(tzinfo=None)
    from datetime import timedelta
    next_test_time = next_test_time + timedelta(seconds=900)

    return SpeedTestResponse(
        result=speed_test_record,
        rate_limit_reset=next_test_time,
    )


@router.get("/speed-test-history", response_model=SpeedTestHistoryResponse)
async def get_speed_test_history(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
    hours: int = Query(default=168, ge=1, le=720, description="Hours of history to retrieve (default 7d)"),
):
    """
    Get historical speed test results for graphing.

    Returns time-series data of download and upload speeds within the specified time range.
    Default is 168 hours (7 days), maximum is 720 hours (30 days).
    """
    user_id = current_user.id

    # Get historical speed tests
    tests = speedtest_crud.get_speed_test_history(
        db=db,
        user_id=user_id,
        hours=hours,
    )

    # Calculate time range and averages
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    from datetime import timedelta
    start_time = now - timedelta(hours=hours)
    end_time = now

    # Calculate averages for successful tests
    successful_tests = [t for t in tests if t.is_successful and t.download_mbps is not None]
    avg_download = None
    avg_upload = None

    if successful_tests:
        avg_download = sum(t.download_mbps for t in successful_tests) / len(successful_tests)
        upload_tests = [t for t in successful_tests if t.upload_mbps is not None]
        if upload_tests:
            avg_upload = sum(t.upload_mbps for t in upload_tests) / len(upload_tests)

    return SpeedTestHistoryResponse(
        tests=tests,
        start_time=start_time,
        end_time=end_time,
        total_tests=len(tests),
        average_download_mbps=round(avg_download, 2) if avg_download else None,
        average_upload_mbps=round(avg_upload, 2) if avg_upload else None,
    )


@router.get("/speed-test-stats", response_model=SpeedTestStatsResponse)
async def get_speed_test_stats(
    current_user: CurrentActiveUser,
    db: Session = Depends(get_db),
):
    """
    Get speed test statistics and latest result.

    Returns:
    - Latest speed test result
    - Average download/upload speeds for 24h and 7d windows
    - Total test counts for each window
    """
    user_id = current_user.id

    # Get latest test
    latest_test = speedtest_crud.get_latest_speed_test(db=db, user_id=user_id)

    # Get statistics
    stats = speedtest_crud.calculate_speed_test_stats(db=db, user_id=user_id)

    return SpeedTestStatsResponse(
        latest_test=latest_test,
        avg_download_24h=stats.get("avg_download_24h"),
        avg_upload_24h=stats.get("avg_upload_24h"),
        avg_download_7d=stats.get("avg_download_7d"),
        avg_upload_7d=stats.get("avg_upload_7d"),
        test_count_24h=stats.get("test_count_24h", 0),
        test_count_7d=stats.get("test_count_7d", 0),
    )
