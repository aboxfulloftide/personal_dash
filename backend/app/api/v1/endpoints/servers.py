from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, DbSession, verify_api_key
from app.crud.server import (
    create_server,
    delete_server,
    get_containers,
    get_processes,
    get_recent_metrics,
    get_server_by_id_and_user,
    get_servers,
    record_metrics,
    update_server_status,
    upsert_containers,
    upsert_processes,
    create_monitored_process,
    delete_monitored_process,
)
from app.schemas.server import (
    ContainerRecord,
    MessageResponse,
    MetricRecord,
    MetricsPayload,
    ProcessCreate,
    ProcessRecord,
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

    # Upsert process stats
    if payload.processes:
        upsert_processes(db, server.id, payload.processes)

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
    processes = get_processes(db, server_id)

    return ServerDetail(
        server=ServerResponse.model_validate(server),
        recent_metrics=[MetricRecord.model_validate(m) for m in recent_metrics],
        containers=[ContainerRecord.model_validate(c) for c in containers],
        processes=[ProcessRecord.model_validate(p) for p in processes],
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


@router.get("/{server_id}/processes-config", response_model=list[ProcessRecord])
def get_process_config(
    server_id: int,
    db: DbSession,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get the list of processes to monitor (for agent).

    Authentication: X-API-Key header verified against server's api_key_hash.
    """
    # Verify API key for the specified server
    server = verify_api_key(server_id, db, x_api_key)

    processes = get_processes(db, server.id)
    return [ProcessRecord.model_validate(p) for p in processes]


@router.post("/{server_id}/processes", response_model=ProcessRecord, status_code=status.HTTP_201_CREATED)
def add_monitored_process(
    server_id: int,
    process_in: ProcessCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a new process to monitor."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    process = create_monitored_process(db, server_id, process_in)
    return ProcessRecord.model_validate(process)


@router.delete("/{server_id}/processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_monitored_process(
    server_id: int,
    process_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Remove a monitored process."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not delete_monitored_process(db, process_id):
        raise HTTPException(status_code=404, detail="Process not found")


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
