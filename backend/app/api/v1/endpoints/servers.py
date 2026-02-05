from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, DbSession, verify_api_key
from app.crud.server import (
    create_server,
    delete_server,
    get_containers,
    get_recent_metrics,
    get_server_by_id_and_user,
    get_servers,
    record_metrics,
    update_server_status,
    upsert_containers,
)
from app.schemas.server import (
    ContainerRecord,
    MessageResponse,
    MetricRecord,
    MetricsPayload,
    ServerCreate,
    ServerCreateResponse,
    ServerDetail,
    ServerResponse,
)

router = APIRouter(prefix="/servers", tags=["Servers"])


# =============================================================================
# Agent endpoint (API key authentication)
# =============================================================================


@router.post("/metrics/report", response_model=MessageResponse)
def report_metrics(
    payload: MetricsPayload,
    db: DbSession,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Receive metrics from a server agent.

    Authentication: X-API-Key header verified against server's api_key_hash.
    """
    # Verify API key for the specified server
    server = verify_api_key(payload.server_id, db, x_api_key)

    # Record metrics
    record_metrics(db, server.id, payload.metrics)

    # Upsert container stats
    if payload.containers:
        upsert_containers(db, server.id, payload.containers)

    # Update server online status
    update_server_status(db, server.id, is_online=True)

    return MessageResponse(message="Metrics recorded")


# =============================================================================
# User endpoints (JWT authentication)
# =============================================================================


@router.post("", response_model=ServerCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_server(
    server_in: ServerCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Register a new server.

    Returns the server details and the raw API key.
    The API key is only shown once - save it immediately.
    """
    server, api_key = create_server(db, current_user.id, server_in)
    return ServerCreateResponse(
        server=ServerResponse.model_validate(server),
        api_key=api_key,
    )


@router.get("", response_model=list[ServerResponse])
def list_servers(
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """List all servers for the current user."""
    servers = get_servers(db, current_user.id)
    return [ServerResponse.model_validate(s) for s in servers]


@router.get("/{server_id}", response_model=ServerDetail)
def get_server_detail(
    server_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a server with recent metrics and container stats."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    recent_metrics = get_recent_metrics(db, server_id, limit=60)
    containers = get_containers(db, server_id)

    return ServerDetail(
        server=ServerResponse.model_validate(server),
        recent_metrics=[MetricRecord.model_validate(m) for m in recent_metrics],
        containers=[ContainerRecord.model_validate(c) for c in containers],
    )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_server(
    server_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a server."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    delete_server(db, server_id)


@router.post("/{server_id}/wake", response_model=MessageResponse)
def wake_server(
    server_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Send Wake-on-LAN packet to server (stub)."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not server.mac_address:
        raise HTTPException(status_code=400, detail="Server has no MAC address configured")

    # TODO: Implement actual WoL packet sending
    return MessageResponse(message=f"Wake-on-LAN not yet implemented for {server.mac_address}")
