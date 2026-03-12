"""
Router poller: ping + optional SSH script execution.
Called by the background scheduler and the on-demand /poll endpoint.
"""
import io
import logging
import subprocess
import time

import paramiko
from sqlalchemy.orm import Session

from app.crud.router import record_poll_result, get_router_ssh_password
from app.models.router import Router, RouterPollResult

logger = logging.getLogger(__name__)


def _ping(hostname: str, timeout: int = 3) -> float | None:
    """Ping hostname once. Returns round-trip ms or None if unreachable."""
    try:
        start = time.monotonic()
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), hostname],
            capture_output=True, timeout=timeout + 1,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        if result.returncode == 0:
            return round(elapsed_ms, 1)
    except Exception:
        pass
    return None


def _run_script_ssh(router: Router) -> str:
    """SSH into the router and run its script. Returns combined stdout+stderr."""
    if not router.script or not router.script.strip():
        return ""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        connect_kwargs = {
            "hostname": router.hostname,
            "port": router.ssh_port,
            "username": router.ssh_user,
            "timeout": 10,
        }
        if router.ssh_key:
            try:
                pkey = paramiko.RSAKey.from_private_key(io.StringIO(router.ssh_key))
                connect_kwargs["pkey"] = pkey
            except Exception:
                # Try Ed25519 / ECDSA if RSA fails
                try:
                    pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(router.ssh_key))
                    connect_kwargs["pkey"] = pkey
                except Exception:
                    pkey = paramiko.ECDSAKey.from_private_key(io.StringIO(router.ssh_key))
                    connect_kwargs["pkey"] = pkey
        else:
            password = get_router_ssh_password(router)
            connect_kwargs["password"] = password

        ssh.connect(**connect_kwargs)
        _, stdout, stderr = ssh.exec_command(router.script, timeout=30)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        return (out + err).strip()
    except Exception as e:
        return f"SSH error: {e}"
    finally:
        ssh.close()


def poll_router(db: Session, router: Router) -> RouterPollResult:
    """Ping the router and optionally run the SSH script. Stores and returns the result."""
    ping_ms = _ping(router.hostname)
    is_online = ping_ms is not None

    script_output = None
    if is_online and router.script and router.script.strip():
        try:
            script_output = _run_script_ssh(router)
        except Exception as e:
            script_output = f"Error: {e}"
            logger.error(f"Router {router.id} script failed: {e}")

    return record_poll_result(db, router, is_online, ping_ms, script_output)
