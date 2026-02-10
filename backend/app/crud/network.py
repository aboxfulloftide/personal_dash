from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

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
