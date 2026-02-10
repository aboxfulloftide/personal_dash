import asyncio
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, get_db
from app.crud import network as network_crud
from app.schemas.network import NetworkStatusRequest, NetworkStatusResponse
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
