from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.models.network import NetworkStatus, NetworkPingResult


def create_network_status(
    db: Session,
    user_id: int,
    status: str,
    ip_address: str | None = None,
    isp: str | None = None,
    location: str | None = None,
) -> NetworkStatus:
    """Create a new network status record."""
    network_status = NetworkStatus(
        user_id=user_id,
        status=status,
        ip_address=ip_address,
        isp=isp,
        location=location,
    )
    db.add(network_status)
    db.commit()
    db.refresh(network_status)
    return network_status


def create_ping_result(
    db: Session,
    user_id: int,
    target_host: str,
    target_name: str | None,
    latency_ms: float | None,
    jitter_ms: float | None,
    packet_loss_pct: float | None,
    is_reachable: bool,
) -> NetworkPingResult:
    """Create a new ping result record."""
    ping_result = NetworkPingResult(
        user_id=user_id,
        target_host=target_host,
        target_name=target_name,
        latency_ms=latency_ms,
        jitter_ms=jitter_ms,
        packet_loss_pct=packet_loss_pct,
        is_reachable=is_reachable,
    )
    db.add(ping_result)
    db.commit()
    db.refresh(ping_result)
    return ping_result


def get_latest_network_status(db: Session, user_id: int) -> NetworkStatus | None:
    """Get the most recent network status for a user."""
    result = db.execute(
        select(NetworkStatus)
        .where(NetworkStatus.user_id == user_id)
        .order_by(desc(NetworkStatus.timestamp))
        .limit(1)
    )
    return result.scalar_one_or_none()


def get_recent_ping_results(
    db: Session, user_id: int, hours: int = 1
) -> list[NetworkPingResult]:
    """Get recent ping results for a user within the last N hours."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = db.execute(
        select(NetworkPingResult)
        .where(
            NetworkPingResult.user_id == user_id,
            NetworkPingResult.timestamp >= cutoff,
        )
        .order_by(desc(NetworkPingResult.timestamp))
    )
    return list(result.scalars().all())


def get_latest_ping_results_per_target(
    db: Session, user_id: int
) -> list[NetworkPingResult]:
    """Get the most recent ping result for each unique target host."""
    # Get distinct target hosts
    targets_result = db.execute(
        select(NetworkPingResult.target_host)
        .where(NetworkPingResult.user_id == user_id)
        .distinct()
    )
    targets = [row[0] for row in targets_result.all()]

    # Get latest result for each target
    results = []
    for target in targets:
        result = db.execute(
            select(NetworkPingResult)
            .where(
                NetworkPingResult.user_id == user_id,
                NetworkPingResult.target_host == target,
            )
            .order_by(desc(NetworkPingResult.timestamp))
            .limit(1)
        )
        ping_result = result.scalar_one_or_none()
        if ping_result:
            results.append(ping_result)

    return results


def get_ping_history(
    db: Session,
    user_id: int,
    hours: int = 24,
    target_host: str | None = None,
) -> dict[str, list[NetworkPingResult]]:
    """
    Get historical ping results grouped by target host.

    Returns a dict mapping target_host -> list of ping results (oldest first).
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)

    # Build query
    query = select(NetworkPingResult).where(
        NetworkPingResult.user_id == user_id,
        NetworkPingResult.timestamp >= cutoff,
    )

    # Filter by specific target if provided
    if target_host:
        query = query.where(NetworkPingResult.target_host == target_host)

    # Order chronologically for graphing
    query = query.order_by(NetworkPingResult.timestamp.asc())

    result = db.execute(query)
    all_results = list(result.scalars().all())

    # Group by target host
    grouped: dict[str, list[NetworkPingResult]] = {}
    for ping_result in all_results:
        if ping_result.target_host not in grouped:
            grouped[ping_result.target_host] = []
        grouped[ping_result.target_host].append(ping_result)

    return grouped


def calculate_uptime_stats(
    db: Session, user_id: int
) -> dict[str, dict[str, float | int]]:
    """
    Calculate uptime statistics for each target over 24h, 7d, and 30d windows.

    Returns a dict mapping target_host -> stats dict with uptime percentages and check counts.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Get distinct target hosts
    targets_result = db.execute(
        select(NetworkPingResult.target_host, NetworkPingResult.target_name)
        .where(NetworkPingResult.user_id == user_id)
        .distinct()
    )
    targets = {row[0]: row[1] for row in targets_result.all()}

    stats = {}

    for target_host, target_name in targets.items():
        target_stats = {"target_name": target_name}

        # Calculate for each time window
        for days, label in [(1, "24h"), (7, "7d"), (30, "30d")]:
            cutoff = now - timedelta(days=days)

            # Count total checks and successful checks
            total_result = db.execute(
                select(func.count(NetworkPingResult.id))
                .where(
                    NetworkPingResult.user_id == user_id,
                    NetworkPingResult.target_host == target_host,
                    NetworkPingResult.timestamp >= cutoff,
                )
            )
            total_checks = total_result.scalar() or 0

            successful_result = db.execute(
                select(func.count(NetworkPingResult.id))
                .where(
                    NetworkPingResult.user_id == user_id,
                    NetworkPingResult.target_host == target_host,
                    NetworkPingResult.timestamp >= cutoff,
                    NetworkPingResult.is_reachable == True,
                )
            )
            successful_checks = successful_result.scalar() or 0

            # Calculate uptime percentage
            uptime_pct = (successful_checks / total_checks * 100) if total_checks > 0 else 0.0

            target_stats[f"uptime_{label}"] = uptime_pct
            target_stats[f"total_checks_{label}"] = total_checks
            target_stats[f"successful_checks_{label}"] = successful_checks

        stats[target_host] = target_stats

    return stats


def cleanup_old_ping_results(db: Session, days: int = 30) -> int:
    """
    Delete ping results older than the specified number of days.

    Returns the number of records deleted.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    # Count records to delete
    count_result = db.execute(
        select(func.count(NetworkPingResult.id))
        .where(NetworkPingResult.timestamp < cutoff)
    )
    count = count_result.scalar() or 0

    # Delete old records
    if count > 0:
        db.execute(
            NetworkPingResult.__table__.delete()
            .where(NetworkPingResult.timestamp < cutoff)
        )
        db.commit()

    return count
