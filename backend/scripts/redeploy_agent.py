#!/usr/bin/env python3
import argparse
import os
import io

import paramiko

from app.core.config import settings
from app.core.database import SessionLocal
from app.crud.server import get_server_ssh_password, get_server_sudo_password
from app.models.server import Server


def load_agent_script() -> str:
    agent_path = os.path.join(os.path.dirname(__file__), "..", "..", "agent", "dash_agent.py")
    agent_path = os.path.normpath(agent_path)
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Agent script not found at {agent_path}")
    with open(agent_path, "r") as f:
        return f.read()


def resolve_server(db, server_id: int | None, name: str | None) -> Server:
    if server_id is not None:
        server = db.get(Server, server_id)
        if not server:
            raise SystemExit(f"Server id {server_id} not found")
        return server
    if name:
        server = db.query(Server).filter(Server.name == name).first()
        if not server:
            raise SystemExit(f"Server named '{name}' not found")
        return server
    raise SystemExit("Must provide --id or --name")


def deploy(server: Server, backend_url: str | None, install_dir: str, env_dir: str) -> None:
    ssh_host = server.ssh_host or server.hostname or server.ip_address
    if not ssh_host:
        raise SystemExit("Server has no ssh_host/hostname/ip_address set")
    ssh_user = server.ssh_user or "root"
    ssh_port = server.ssh_port or 22

    ssh_password = get_server_ssh_password(server)
    ssh_key = server.ssh_key
    if not ssh_password and not ssh_key:
        raise SystemExit("Server has no SSH credentials set")

    agent_script = load_agent_script()
    dash_api_url = (backend_url or f"{settings.BACKEND_URL}/api/v1").rstrip("/")
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
EnvironmentFile={env_dir}/agent.env
ExecStart={install_dir}/venv/bin/python3 {install_dir}/dash_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        "hostname": ssh_host,
        "port": ssh_port,
        "username": ssh_user,
        "timeout": 15,
    }
    if ssh_key:
        pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key))
        connect_kwargs["pkey"] = pkey
    else:
        connect_kwargs["password"] = ssh_password

    ssh.connect(**connect_kwargs)
    try:
        sudo_pass = get_server_sudo_password(server) or ssh_password or ""

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

        def step(cmd: str) -> None:
            out, err, code = run(cmd)
            if code != 0:
                out, err, code = run_sudo(cmd)
            if code != 0:
                raise SystemExit(f"Command failed: {cmd}\n{err or out}")

        def read_file_text(remote_path: str) -> str | None:
            try:
                with sftp.open(remote_path, "r") as f:
                    return f.read().decode()
            except Exception:
                pass
            stdin2, stdout2, _ = ssh.exec_command(f"sudo -S -p '' cat {remote_path}")
            if sudo_pass:
                stdin2.write(sudo_pass + "\n")
                stdin2.flush()
            if stdout2.channel.recv_exit_status() == 0:
                return stdout2.read().decode()
            return None

        def write_file_sudo(remote_path: str, content: str, mode: str = "644") -> None:
            import uuid
            tmp = f"/tmp/dash_deploy_{uuid.uuid4().hex[:8]}"
            with sftp.open(tmp, "w") as f:
                f.write(content)
            move_cmd = f"mv {tmp} {remote_path} && chmod {mode} {remote_path}"
            out, err, code = run(move_cmd)
            if code != 0:
                out, err, code = run_sudo(move_cmd)
            if code != 0:
                raise SystemExit(f"Write failed: {err or out}")

        step(f"mkdir -p {install_dir}")
        step(f"mkdir -p {env_dir}")

        sftp = ssh.open_sftp()
        try:
            write_file_sudo(f"{install_dir}/dash_agent.py", agent_script, mode="755")

            existing_api_key = None
            env_file_path = f"{env_dir}/agent.env"
            existing_content = read_file_text(env_file_path)
            if existing_content:
                for line in existing_content.splitlines():
                    line = line.strip()
                    if line.startswith("DASH_API_KEY=") and not line.endswith("="):
                        existing_api_key = line.split("=", 1)[1].strip()
                        break

            final_env = env_content.replace(
                "# DASH_API_KEY=<paste-your-api-key-here>",
                f"DASH_API_KEY={existing_api_key}" if existing_api_key else "# DASH_API_KEY=<paste-your-api-key-here>",
            )
            write_file_sudo(env_file_path, final_env, mode="600")

            write_file_sudo("/etc/systemd/system/dash-agent.service", systemd_service, mode="644")

            step("systemctl daemon-reload")
            step("systemctl enable dash-agent")
            step("systemctl restart dash-agent")
        finally:
            sftp.close()
    finally:
        ssh.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Redeploy dash agent using stored SSH credentials.")
    parser.add_argument("--id", type=int, help="Server ID")
    parser.add_argument("--name", type=str, help="Server name")
    parser.add_argument("--backend-url", type=str, help="Override backend URL")
    parser.add_argument("--install-dir", type=str, default="/opt/dash-agent")
    parser.add_argument("--env-dir", type=str, default="/etc/dash-agent")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        server = resolve_server(db, args.id, args.name)
        deploy(server, args.backend_url, args.install_dir, args.env_dir)
        print("Redeploy complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
