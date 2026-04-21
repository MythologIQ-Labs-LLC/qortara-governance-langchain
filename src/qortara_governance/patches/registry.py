"""Patch lifecycle registry — install all patches at init, unpatch at teardown.

Maintains ONE patch set per process. Re-invoking `apply_patches` with the same
client is a no-op (idempotent). Re-invoking with a different client raises
unless `unpatch_all` is called first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qortara_governance.client import SidecarClient
from qortara_governance.patches import langgraph_patches, tool_patches


@dataclass
class _PatchSet:
    client: SidecarClient | None = None
    tool_originals: dict[str, Any] = field(default_factory=dict)
    langgraph_originals: dict[str, Any] | None = None
    installed: bool = False


_STATE = _PatchSet()


def apply_patches(client: SidecarClient) -> None:
    """Install BaseTool + (optional) ToolNode patches. Idempotent per client."""
    if _STATE.installed:
        if _STATE.client is client:
            return
        raise RuntimeError(
            "Qortara patches already installed with a different client. "
            "Call qortara_governance.unpatch_all() first."
        )
    _STATE.tool_originals = tool_patches.apply(client)
    _STATE.langgraph_originals = langgraph_patches.apply(client)
    _STATE.client = client
    _STATE.installed = True


def unpatch_all() -> None:
    """Restore byte-identical originals. Required for test teardown."""
    if not _STATE.installed:
        return
    tool_patches.unpatch(_STATE.tool_originals)
    langgraph_patches.unpatch(_STATE.langgraph_originals)
    if _STATE.client is not None:
        _STATE.client.close()
    _STATE.client = None
    _STATE.tool_originals = {}
    _STATE.langgraph_originals = None
    _STATE.installed = False


def is_patched() -> bool:
    """Return True iff patches are currently applied."""
    return _STATE.installed


def get_client() -> SidecarClient | None:
    """Return the currently-installed client, or None."""
    return _STATE.client
