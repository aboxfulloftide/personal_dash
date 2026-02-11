import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.server import Server, ServerMetric, DockerContainer, MonitoredProcess, MonitoredDrive
from app.schemas.server import ServerCreate, MetricsData, ContainerInfo, ProcessInfo, ProcessCreate, DriveInfo, DriveCreate
from app.core.security import get_password_hash


def generate_api_key() -> str:
    """Generate a secure API key (43 chars, 256 bits entropy)."""
    return secrets.token_urlsafe(32)


def create_server(db: Session, user_id: int, server_in: ServerCreate) -> tuple[Server, str]:
    """Create a new server and return (server, raw_api_key)."""
    raw_api_key = generate_api_key()
    api_key_hash = get_password_hash(raw_api_key)

    server = Server(
        user_id=user_id,
        name=server_in.name,
        hostname=server_in.hostname,
        ip_address=server_in.ip_address,
        mac_address=server_in.mac_address,
        poll_interval=server_in.poll_interval,
        api_key_hash=api_key_hash,
        is_online=False,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server, raw_api_key


def get_servers(db: Session, user_id: int) -> list[Server]:
    """Get all servers for a user."""
    result = db.execute(
        select(Server).where(Server.user_id == user_id).order_by(Server.created_at.desc())
    )
    return list(result.scalars().all())


def get_server(db: Session, server_id: int) -> Server | None:
    """Get a server by ID."""
    return db.get(Server, server_id)


def get_server_by_id_and_user(db: Session, server_id: int, user_id: int) -> Server | None:
    """Get a server by ID with ownership check."""
    result = db.execute(
        select(Server).where(Server.id == server_id, Server.user_id == user_id)
    )
    return result.scalar_one_or_none()


def delete_server(db: Session, server_id: int) -> bool:
    """Delete a server. Returns True if deleted, False if not found."""
    server = db.get(Server, server_id)
    if not server:
        return False
    db.delete(server)
    db.commit()
    return True


def update_server_status(db: Session, server_id: int, is_online: bool) -> None:
    """Update server online status and last_seen timestamp."""
    server = db.get(Server, server_id)
    if server:
        server.is_online = is_online
        server.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()


def record_metrics(db: Session, server_id: int, metrics: MetricsData) -> ServerMetric:
    """Insert a new metrics record."""
    metric = ServerMetric(
        server_id=server_id,
        cpu_percent=metrics.cpu_percent,
        memory_percent=metrics.memory_percent,
        disk_percent=metrics.disk_percent,
        network_in=metrics.network_in,
        network_out=metrics.network_out,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def upsert_containers(db: Session, server_id: int, containers: list[ContainerInfo]) -> None:
    """Upsert container records for a server."""
    # Get existing containers for this server
    existing = db.execute(
        select(DockerContainer).where(DockerContainer.server_id == server_id)
    )
    existing_map = {c.container_id: c for c in existing.scalars().all()}

    seen_ids = set()
    for container in containers:
        seen_ids.add(container.container_id)

        if container.container_id in existing_map:
            # Update existing
            existing_container = existing_map[container.container_id]
            existing_container.name = container.name
            existing_container.image = container.image
            existing_container.status = container.status
            existing_container.cpu_percent = container.cpu_percent
            existing_container.memory_usage = container.memory_usage
            existing_container.memory_limit = container.memory_limit
        else:
            # Insert new
            new_container = DockerContainer(
                server_id=server_id,
                container_id=container.container_id,
                name=container.name,
                image=container.image,
                status=container.status,
                cpu_percent=container.cpu_percent,
                memory_usage=container.memory_usage,
                memory_limit=container.memory_limit,
            )
            db.add(new_container)

    # Remove containers that no longer exist
    for container_id, container in existing_map.items():
        if container_id not in seen_ids:
            db.delete(container)

    db.commit()


def get_recent_metrics(db: Session, server_id: int, limit: int = 60) -> list[ServerMetric]:
    """Get the most recent metrics for a server."""
    result = db.execute(
        select(ServerMetric)
        .where(ServerMetric.server_id == server_id)
        .order_by(ServerMetric.recorded_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def get_containers(db: Session, server_id: int) -> list[DockerContainer]:
    """Get all containers for a server."""
    result = db.execute(
        select(DockerContainer).where(DockerContainer.server_id == server_id)
    )
    return list(result.scalars().all())


def upsert_processes(db: Session, server_id: int, processes: list[ProcessInfo]) -> None:
    """Upsert process records for a server."""
    # Get existing processes for this server
    existing = db.execute(
        select(MonitoredProcess).where(MonitoredProcess.server_id == server_id)
    )
    existing_map = {p.match_pattern: p for p in existing.scalars().all()}

    for process in processes:
        if process.match_pattern in existing_map:
            # Update existing
            existing_process = existing_map[process.match_pattern]
            existing_process.is_running = process.is_running
            existing_process.cpu_percent = process.cpu_percent
            existing_process.memory_mb = process.memory_mb
            existing_process.pid = process.pid
            existing_process.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()


def get_processes(db: Session, server_id: int) -> list[MonitoredProcess]:
    """Get all monitored processes for a server."""
    result = db.execute(
        select(MonitoredProcess).where(MonitoredProcess.server_id == server_id)
    )
    return list(result.scalars().all())


def create_monitored_process(db: Session, server_id: int, process_in: ProcessCreate) -> MonitoredProcess:
    """Create a new monitored process."""
    process = MonitoredProcess(
        server_id=server_id,
        process_name=process_in.process_name,
        match_pattern=process_in.match_pattern,
        is_running=False,
    )
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


def delete_monitored_process(db: Session, process_id: int) -> bool:
    """Delete a monitored process. Returns True if deleted, False if not found."""
    process = db.get(MonitoredProcess, process_id)
    if not process:
        return False
    db.delete(process)
    db.commit()
    return True


def upsert_drives(db: Session, server_id: int, drives: list[DriveInfo]) -> None:
    """Upsert drive records for a server."""
    # Get existing drives for this server
    existing = db.execute(
        select(MonitoredDrive).where(MonitoredDrive.server_id == server_id)
    )
    existing_map = {d.mount_point: d for d in existing.scalars().all()}

    for drive in drives:
        if drive.mount_point in existing_map:
            # Update existing
            existing_drive = existing_map[drive.mount_point]
            existing_drive.device = drive.device
            existing_drive.fstype = drive.fstype
            existing_drive.total_bytes = drive.total_bytes
            existing_drive.used_bytes = drive.used_bytes
            existing_drive.free_bytes = drive.free_bytes
            existing_drive.percent_used = drive.percent_used
            existing_drive.is_mounted = drive.is_mounted
            existing_drive.is_readonly = drive.is_readonly
            existing_drive.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()


def get_drives(db: Session, server_id: int) -> list[MonitoredDrive]:
    """Get all monitored drives for a server."""
    result = db.execute(
        select(MonitoredDrive).where(MonitoredDrive.server_id == server_id)
    )
    return list(result.scalars().all())


def create_monitored_drive(db: Session, server_id: int, drive_in: DriveCreate) -> MonitoredDrive:
    """Create a new monitored drive."""
    drive = MonitoredDrive(
        server_id=server_id,
        mount_point=drive_in.mount_point,
        is_mounted=False,
    )
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive


def delete_monitored_drive(db: Session, drive_id: int) -> bool:
    """Delete a monitored drive. Returns True if deleted, False if not found."""
    drive = db.get(MonitoredDrive, drive_id)
    if not drive:
        return False
    db.delete(drive)
    db.commit()
    return True
