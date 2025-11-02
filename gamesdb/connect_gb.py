"""Utilities for opening an SSH session against the configured device."""

from __future__ import annotations

import subprocess

import gamesdb

SSH_OPTIONS = [
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "UserKnownHostsFile=/dev/null",
]


def _resolve_host(server_cfg: dict[str, object], host_override: str | None) -> str:
    if host_override:
        return host_override

    host = server_cfg.get("ip") or server_cfg.get("name")
    if not isinstance(host, str) or not host:
        raise RuntimeError("Server host is not defined in configuration.")
    return host


def _resolve_user(server_cfg: dict[str, object], user_override: str | None) -> str:
    if user_override:
        return user_override

    user = server_cfg.get("user", "root")
    if not isinstance(user, str) or not user:
        raise RuntimeError("Server user is not defined in configuration.")
    return user


def _resolve_port(server_cfg: dict[str, object], port_override: int | None) -> int | None:
    if port_override is not None:
        return port_override

    port = server_cfg.get("port")
    if isinstance(port, int):
        return port
    if isinstance(port, str) and port.isdigit():
        return int(port)
    return None


def connect_to_device(
    host: str | None = None,
    user: str | None = None,
    port: int | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Open an interactive SSH session using the packaged configuration."""
    server_cfg = gamesdb.GAMESDB_CONFIG.get("server", {})
    if not isinstance(server_cfg, dict):
        raise RuntimeError("Server configuration is missing or invalid.")

    resolved_host = _resolve_host(server_cfg, host)
    resolved_user = _resolve_user(server_cfg, user)
    resolved_port = _resolve_port(server_cfg, port)

    command = ["ssh"]
    if resolved_port:
        command.extend(["-p", str(resolved_port)])
    command.extend(SSH_OPTIONS)
    command.append(f"{resolved_user}@{resolved_host}")

    return subprocess.run(command, check=True)


if __name__ == "__main__":
    connect_to_device()
