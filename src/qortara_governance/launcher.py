"""Subprocess launcher for auto-spawning the sidecar binary.

If QORTARA_SIDECAR_ENDPOINT is set, skips spawn and connects to an existing
daemon. Otherwise spawns `qortara-governance-sidecar` as a subprocess bound
to 127.0.0.1 on an OS-assigned port.
"""

from __future__ import annotations

import atexit
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass

from qortara_governance.exceptions import QortaraSidecarUnavailable

_SPAWN_WAIT_S = 10.0
_SPAWN_POLL_S = 0.25


@dataclass
class LaunchResult:
    endpoint: str
    spawned: (
        bool  # True iff we own the subprocess; False if connected to external daemon
    )
    process: subprocess.Popen[bytes] | None = None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_ready(endpoint: str) -> bool:
    # Poll until a TCP connection succeeds or timeout.
    host, port = endpoint.removeprefix("http://").split(":")
    deadline = time.time() + _SPAWN_WAIT_S
    while time.time() < deadline:
        try:
            with socket.create_connection((host, int(port)), timeout=1.0):
                return True
        except OSError:
            time.sleep(_SPAWN_POLL_S)
    return False


def launch(*, existing_endpoint: str | None) -> LaunchResult:
    """Resolve a working sidecar endpoint.

    If `existing_endpoint` is provided, treat as external daemon and verify
    reachability. Otherwise spawn a subprocess.
    """
    if existing_endpoint:
        return LaunchResult(endpoint=existing_endpoint, spawned=False)

    binary = shutil.which("qortara-governance-sidecar")
    if not binary:
        raise QortaraSidecarUnavailable(
            "qortara-governance-sidecar binary not found on PATH. "
            "Install 'qortara-governance-sidecar' OR set QORTARA_SIDECAR_ENDPOINT."
        )

    port = _free_port()
    endpoint = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [binary, "--host", "127.0.0.1", "--port", str(port)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not _wait_for_ready(endpoint):
        proc.terminate()
        raise QortaraSidecarUnavailable(
            f"sidecar subprocess did not become reachable on {endpoint} within {_SPAWN_WAIT_S}s"
        )

    def _shutdown() -> None:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, OSError):
                proc.kill()

    atexit.register(_shutdown)
    return LaunchResult(endpoint=endpoint, spawned=True, process=proc)
