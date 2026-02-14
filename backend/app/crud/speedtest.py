from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.models.network import SpeedTestResult


def create_speed_test_result(
    db: Session,
    user_id: int,
    download_mbps: float | None = None,
    upload_mbps: float | None = None,
    ping_ms: float | None = None,
    server_id: str | None = None,
    server_name: str | None = None,
    server_location: str | None = None,
    server_sponsor: str | None = None,
    test_duration_seconds: float | None = None,
    is_successful: bool = False,
    error_message: str | None = None,
) -> SpeedTestResult:
    """Create a new speed test result record."""
    speed_test = SpeedTestResult(
        user_id=user_id,
        download_mbps=download_mbps,
        upload_mbps=upload_mbps,
        ping_ms=ping_ms,
        server_id=server_id,
        server_name=server_name,
        server_location=server_location,
        server_sponsor=server_sponsor,
        test_duration_seconds=test_duration_seconds,
        is_successful=is_successful,
        error_message=error_message,
    )
    db.add(speed_test)
    db.commit()
    db.refresh(speed_test)
    return speed_test


def get_latest_speed_test(db: Session, user_id: int) -> SpeedTestResult | None:
    """Get the most recent speed test result for a user."""
    result = db.execute(
        select(SpeedTestResult)
        .where(SpeedTestResult.user_id == user_id)
        .order_by(desc(SpeedTestResult.timestamp))
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_speed_test_history(
    db: Session, user_id: int, hours: int = 168
) -> list[SpeedTestResult]:
    """
    Get speed test history for a user within the last N hours.
    Default is 168 hours (7 days).
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = db.execute(
        select(SpeedTestResult)
        .where(
            SpeedTestResult.user_id == user_id,
            SpeedTestResult.timestamp >= cutoff,
        )
        .order_by(SpeedTestResult.timestamp.asc())  # Chronological for graphing
    )
    return list(result.scalars().all())


def calculate_speed_test_stats(db: Session, user_id: int) -> dict:
    """
    Calculate speed test statistics over different time windows.

    Returns averages for download/upload speeds over 24h and 7d windows,
    plus total test counts.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stats = {}

    # Calculate for each time window
    for days, label in [(1, "24h"), (7, "7d")]:
        cutoff = now - timedelta(days=days)

        # Get count of successful tests
        count_result = db.execute(
            select(func.count(SpeedTestResult.id))
            .where(
                SpeedTestResult.user_id == user_id,
                SpeedTestResult.timestamp >= cutoff,
                SpeedTestResult.is_successful == True,
            )
        )
        test_count = count_result.scalar() or 0

        # Get average download speed
        avg_download_result = db.execute(
            select(func.avg(SpeedTestResult.download_mbps))
            .where(
                SpeedTestResult.user_id == user_id,
                SpeedTestResult.timestamp >= cutoff,
                SpeedTestResult.is_successful == True,
                SpeedTestResult.download_mbps.isnot(None),
            )
        )
        avg_download = avg_download_result.scalar()

        # Get average upload speed
        avg_upload_result = db.execute(
            select(func.avg(SpeedTestResult.upload_mbps))
            .where(
                SpeedTestResult.user_id == user_id,
                SpeedTestResult.timestamp >= cutoff,
                SpeedTestResult.is_successful == True,
                SpeedTestResult.upload_mbps.isnot(None),
            )
        )
        avg_upload = avg_upload_result.scalar()

        stats[f"avg_download_{label}"] = round(avg_download, 2) if avg_download else None
        stats[f"avg_upload_{label}"] = round(avg_upload, 2) if avg_upload else None
        stats[f"test_count_{label}"] = test_count

    return stats


def check_rate_limit(
    db: Session, user_id: int, min_interval_seconds: int = 900
) -> tuple[bool, datetime | None]:
    """
    Check if user is rate limited for speed tests.

    Args:
        db: Database session
        user_id: User ID
        min_interval_seconds: Minimum seconds between tests (default 900 = 15 minutes)

    Returns:
        Tuple of (is_rate_limited, rate_limit_reset_time)
        - is_rate_limited: True if user must wait before next test
        - rate_limit_reset_time: When they can test again (None if not limited)
    """
    latest_test = get_latest_speed_test(db, user_id)

    if not latest_test:
        return False, None

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    time_since_last_test = now - latest_test.timestamp
    min_interval = timedelta(seconds=min_interval_seconds)

    if time_since_last_test < min_interval:
        reset_time = latest_test.timestamp + min_interval
        return True, reset_time
    else:
        return False, None


def cleanup_old_speed_tests(db: Session, days: int = 90) -> int:
    """
    Delete speed test results older than the specified number of days.

    Returns the number of records deleted.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    # Count records to delete
    count_result = db.execute(
        select(func.count(SpeedTestResult.id))
        .where(SpeedTestResult.timestamp < cutoff)
    )
    count = count_result.scalar() or 0

    # Delete old records
    if count > 0:
        db.execute(
            SpeedTestResult.__table__.delete()
            .where(SpeedTestResult.timestamp < cutoff)
        )
        db.commit()

    return count
