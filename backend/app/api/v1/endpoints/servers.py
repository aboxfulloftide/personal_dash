from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentActiveUser, DbSession, verify_api_key
from app.crud.server import (
    create_server,
    delete_server,
    get_containers,
    get_processes,
    get_drives,
    get_metrics_by_timerange,
    get_recent_metrics,
    get_server_by_id_and_user,
    get_servers,
    record_metrics,
    update_server_status,
    upsert_containers,
    upsert_processes,
    upsert_drives,
    create_monitored_process,
    delete_monitored_process,
    create_monitored_drive,
    delete_monitored_drive,
    get_process_presets,
    create_process_preset,
    delete_process_preset,
)
from app.schemas.server import (
    ContainerRecord,
    DeployRequest,
    DeployResponse,
    MessageResponse,
    MetricRecord,
    MetricsPayload,
    ProcessCreate,
    ProcessPresetCreate,
    ProcessPresetResponse,
    ProcessRecord,
    DriveCreate,
    DriveRecord,
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

    # Upsert drive stats
    if payload.drives:
        upsert_drives(db, server.id, payload.drives)

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
    drives = get_drives(db, server_id)

    return ServerDetail(
        server=ServerResponse.model_validate(server),
        recent_metrics=[MetricRecord.model_validate(m) for m in recent_metrics],
        containers=[ContainerRecord.model_validate(c) for c in containers],
        processes=[ProcessRecord.model_validate(p) for p in processes],
        drives=[DriveRecord.model_validate(d) for d in drives],
    )


@router.get("/{server_id}/metrics", response_model=list[MetricRecord])
def get_server_metrics_history(
    server_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
    hours: int = Query(1, ge=1, le=168),
):
    """Get historical metrics for a server within the last N hours."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    metrics = get_metrics_by_timerange(db, server_id, hours=hours)
    return [MetricRecord.model_validate(m) for m in metrics]


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


@router.get("/{server_id}/drives-config", response_model=list[DriveRecord])
def get_drives_config(
    server_id: int,
    db: DbSession,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get the list of drives to monitor (for agent).

    Authentication: X-API-Key header verified against server's api_key_hash.
    """
    # Verify API key for the specified server
    server = verify_api_key(server_id, db, x_api_key)

    drives = get_drives(db, server.id)
    return [DriveRecord.model_validate(d) for d in drives]


@router.post("/{server_id}/drives", response_model=DriveRecord, status_code=status.HTTP_201_CREATED)
def add_monitored_drive(
    server_id: int,
    drive_in: DriveCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a new drive to monitor."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    drive = create_monitored_drive(db, server_id, drive_in)
    return DriveRecord.model_validate(drive)


@router.delete("/{server_id}/drives/{drive_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_monitored_drive(
    server_id: int,
    drive_id: int,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Remove a monitored drive."""
    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not delete_monitored_drive(db, drive_id):
        raise HTTPException(status_code=404, detail="Drive not found")


@router.get("/process-presets", response_model=list[ProcessPresetResponse])
def list_process_presets(db: DbSession, current_user: CurrentActiveUser):
    """Get all process presets (builtin + user-defined)."""
    return get_process_presets(db)


@router.post("/process-presets", response_model=ProcessPresetResponse, status_code=status.HTTP_201_CREATED)
def add_process_preset(preset_in: ProcessPresetCreate, db: DbSession, current_user: CurrentActiveUser):
    """Create a user-defined process preset."""
    return create_process_preset(db, preset_in)


@router.delete("/process-presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_process_preset(preset_id: int, db: DbSession, current_user: CurrentActiveUser):
    """Delete a user-defined process preset. Builtin presets cannot be deleted."""
    if not delete_process_preset(db, preset_id):
        raise HTTPException(status_code=404, detail="Preset not found or cannot delete a builtin preset")


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


@router.post("/{server_id}/deploy", response_model=DeployResponse)
def deploy_agent(
    server_id: int,
    deploy_in: DeployRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Deploy the monitoring agent to a remote server via SSH."""
    import io
    import paramiko

    server = get_server_by_id_and_user(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not deploy_in.ssh_password and not deploy_in.ssh_key:
        raise HTTPException(status_code=400, detail="Either ssh_password or ssh_key is required")

    log: list[str] = []

    # Read the agent script from disk
    import os
    agent_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "agent", "dash_agent.py")
    agent_path = os.path.normpath(agent_path)
    if not os.path.exists(agent_path):
        raise HTTPException(status_code=500, detail=f"Agent script not found at {agent_path}")

    with open(agent_path, "r") as f:
        agent_script = f.read()

    # Build env file content
    from app.core.config import settings
    dash_api_url = (deploy_in.backend_url or f"{settings.BACKEND_URL}/api/v1").rstrip("/")
    env_content = f"""# Personal Dash Agent - Auto-deployed
DASH_API_URL={dash_api_url}
DASH_SERVER_ID={server.id}
DASH_POLL_INTERVAL={server.poll_interval}
DASH_COLLECT_DOCKER=true
DASH_COLLECT_PROCESSES=true
DASH_COLLECT_DRIVES=true
DASH_LOG_LEVEL=INFO
# DASH_API_KEY=<paste-your-api-key-here>
"""

    systemd_service = f"""[Unit]
Description=Personal Dash Monitoring Agent ({server.name})
After=network.target

[Service]
Type=simple
User=root
EnvironmentFile={deploy_in.env_dir}/agent.env
ExecStart={deploy_in.install_dir}/venv/bin/python3 {deploy_in.install_dir}/dash_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        connect_kwargs = {
            "hostname": deploy_in.ssh_host,
            "port": deploy_in.ssh_port,
            "username": deploy_in.ssh_user,
            "timeout": 15,
        }
        if deploy_in.ssh_key:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(deploy_in.ssh_key))
            connect_kwargs["pkey"] = pkey
        else:
            connect_kwargs["password"] = deploy_in.ssh_password

        log.append(f"Connecting to {deploy_in.ssh_user}@{deploy_in.ssh_host}:{deploy_in.ssh_port}...")
        ssh.connect(**connect_kwargs)
        log.append("Connected.")

        # sudo password: explicit override → ssh password → none (key auth, try NOPASSWD)
        sudo_pass = deploy_in.sudo_password or deploy_in.ssh_password or ""

        def run(cmd: str) -> tuple[str, str, int]:
            _, stdout, stderr = ssh.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode().strip(), stderr.read().decode().strip(), exit_code

        def run_sudo(cmd: str) -> tuple[str, str, int]:
            stdin, stdout, stderr = ssh.exec_command(f"sudo -S -p '' {cmd}")
            if sudo_pass:
                stdin.write(sudo_pass + "\n")
                stdin.flush()
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode().strip(), stderr.read().decode().strip(), exit_code

        def step(description: str, cmd: str, allow_fail: bool = False) -> bool:
            log.append(f"  {description}")
            log.append(f"    $ {cmd}")
            out, err, code = run(cmd)
            if code != 0:
                log.append(f"    Permission denied or error (exit {code}) — retrying with sudo...")
                log.append(f"    $ sudo {cmd}")
                out, err, code = run_sudo(cmd)
            if code != 0 and not allow_fail:
                log.append(f"    FAILED (exit {code}): {err or out}")
                return False
            if out:
                log.append(f"    {out[:300]}")
            log.append(f"    OK")
            return True

        def read_file_text(remote_path: str) -> str | None:
            """Read a remote file as text, trying SFTP then sudo cat."""
            # Try direct SFTP read first
            try:
                with sftp.open(remote_path, "r") as f:
                    return f.read().decode()
            except Exception:
                pass
            # Fall back to sudo cat
            log.append(f"    Direct read of {remote_path} denied — trying sudo cat...")
            stdin2, stdout2, _ = ssh.exec_command(f"sudo -S -p '' cat {remote_path}")
            if sudo_pass:
                stdin2.write(sudo_pass + "\n")
                stdin2.flush()
            if stdout2.channel.recv_exit_status() == 0:
                return stdout2.read().decode()
            return None

        def write_file_sudo(remote_path: str, content: str, description: str, mode: str = "644") -> bool:
            """Write content to a remote path: SFTP to /tmp, then mv (with sudo fallback)."""
            import uuid
            tmp = f"/tmp/dash_deploy_{uuid.uuid4().hex[:8]}"
            log.append(f"  {description} → {remote_path}")
            log.append(f"    Writing {len(content)} bytes via /tmp staging file...")
            try:
                with sftp.open(tmp, "w") as f:
                    f.write(content)
            except Exception as e:
                log.append(f"    FAILED writing to /tmp: {e}")
                return False

            move_cmd = f"mv {tmp} {remote_path} && chmod {mode} {remote_path}"
            log.append(f"    $ {move_cmd}")
            _, err, code = run(move_cmd)
            if code != 0:
                log.append(f"    Permission denied (exit {code}) — retrying with sudo...")
                log.append(f"    $ sudo {move_cmd}")
                _, err, code = run_sudo(move_cmd)
            if code != 0:
                log.append(f"    FAILED: {err}")
                run(f"rm -f {tmp}")
                return False
            log.append(f"    OK")
            return True

        # Create directories
        if not step(f"Creating install directory {deploy_in.install_dir}", f"mkdir -p {deploy_in.install_dir}"):
            return DeployResponse(success=False, log=log)
        if not step(f"Creating config directory {deploy_in.env_dir}", f"mkdir -p {deploy_in.env_dir}"):
            return DeployResponse(success=False, log=log)

        sftp = ssh.open_sftp()
        try:
            # Upload agent script
            if not write_file_sudo(
                f"{deploy_in.install_dir}/dash_agent.py",
                agent_script,
                "Uploading agent script",
                mode="755",
            ):
                return DeployResponse(success=False, log=log)

            # Check for existing DASH_API_KEY to preserve
            existing_api_key = None
            env_file_path = f"{deploy_in.env_dir}/agent.env"
            log.append(f"  Checking for existing config at {env_file_path}...")
            existing_content = read_file_text(env_file_path)
            if existing_content:
                for line in existing_content.splitlines():
                    line = line.strip()
                    if line.startswith("DASH_API_KEY=") and not line.endswith("="):
                        existing_api_key = line.split("=", 1)[1].strip()
                        break
                if existing_api_key:
                    log.append(f"    Found existing DASH_API_KEY — will preserve it.")
                else:
                    log.append(f"    Config exists but no API key set yet.")
            else:
                log.append(f"    No existing config found — fresh install.")

            final_env = env_content.replace(
                "# DASH_API_KEY=<paste-your-api-key-here>",
                f"DASH_API_KEY={existing_api_key}" if existing_api_key else "# DASH_API_KEY=<paste-your-api-key-here>",
            )
            if not write_file_sudo(env_file_path, final_env, "Writing agent config", mode="600"):
                return DeployResponse(success=False, log=log)
            if existing_api_key:
                log.append("    DASH_API_KEY preserved from previous install.")
            else:
                log.append("    Config written — you must add DASH_API_KEY before starting.")

            # Write systemd service file
            service_path = f"/etc/systemd/system/{deploy_in.service_name}.service"
            if not write_file_sudo(service_path, systemd_service, "Writing systemd service", mode="644"):
                return DeployResponse(success=False, log=log)
        finally:
            sftp.close()

        # Create virtualenv and install dependencies
        venv_dir = f"{deploy_in.install_dir}/venv"
        step("Checking Python 3 version", "python3 --version")
        step(f"Creating virtualenv at {venv_dir}", f"python3 -m venv {venv_dir}")
        step("Installing dependencies", f"{venv_dir}/bin/pip install -q psutil requests")

        # Reload systemd and enable service
        step("Reloading systemd daemon", "systemctl daemon-reload")
        step(f"Enabling {deploy_in.service_name} service", f"systemctl enable {deploy_in.service_name}", allow_fail=True)

        log.append("")
        log.append("=" * 40)
        if existing_api_key:
            log.append("Deployment complete! Restarting service...")
            step(f"Restarting {deploy_in.service_name}", f"systemctl restart {deploy_in.service_name}", allow_fail=True)
            out, _, _ = run(f"systemctl is-active {deploy_in.service_name}")
            log.append(f"Service status: {out or 'unknown'}")
        else:
            log.append("Deployment complete!")
            log.append("")
            log.append("ACTION REQUIRED: Add your API key to the config file:")
            log.append(f"  {deploy_in.env_dir}/agent.env")
            log.append("")
            log.append("  DASH_API_KEY=<your-api-key>")
            log.append("")
            log.append("Then start the agent:")
            log.append(f"  sudo systemctl start {deploy_in.service_name}")

        return DeployResponse(success=True, log=log)

    except paramiko.AuthenticationException:
        log.append("ERROR: Authentication failed. Check username/password or SSH key.")
        return DeployResponse(success=False, log=log)
    except paramiko.SSHException as e:
        log.append(f"ERROR: SSH error: {e}")
        return DeployResponse(success=False, log=log)
    except Exception as e:
        log.append(f"ERROR: {e}")
        return DeployResponse(success=False, log=log)
    finally:
        ssh.close()
