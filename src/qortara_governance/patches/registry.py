"""Patch lifecycle registry — versioned FrameworkAdapter dispatch.

Holds an ordered dict of (adapter, AdapterState) entries. `apply` checks each
adapter's contract_version, attempts to import its target framework (skipping
with a `RuntimeWarning` on failure), and stores the returned state.
`unpatch_all` unwinds stored entries in LIFO order.

The module exposes a process-singleton `_REGISTRY` so the public entry point
`qortara_governance.init()` can remain a thin wrapper.
"""

from __future__ import annotations

import importlib.util
import warnings
from typing import Sequence

from qortara_governance.client import SidecarClient
from qortara_governance.contract.protocol import FrameworkAdapter
from qortara_governance.contract.state import (
    CONTRACT_VERSION,
    AdapterState,
    IncompatibleAdapterVersion,
)


def _default_adapters() -> list[FrameworkAdapter]:
    """Return the default adapter list shipped with this SDK."""
    from qortara_governance.patches.langgraph_patches import LangGraphToolNodeAdapter
    from qortara_governance.patches.tool_patches import LangChainToolAdapter

    return [LangChainToolAdapter(), LangGraphToolNodeAdapter()]


class AdapterRegistry:
    """Ordered registry of applied FrameworkAdapters and their AdapterStates."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[FrameworkAdapter, AdapterState]] = {}
        self._client: SidecarClient | None = None

    def apply(
        self,
        client: SidecarClient,
        adapters: Sequence[FrameworkAdapter],
    ) -> None:
        """Apply each adapter in order; skip those whose framework is unavailable."""
        for adapter in adapters:
            self._apply_one(client, adapter)
        self._client = client

    def _apply_one(self, client: SidecarClient, adapter: FrameworkAdapter) -> None:
        if adapter.contract_version != CONTRACT_VERSION:
            raise IncompatibleAdapterVersion(
                f"adapter {adapter.name!r} contract_version="
                f"{adapter.contract_version!r} does not match "
                f"CONTRACT_VERSION={CONTRACT_VERSION!r}"
            )
        try:
            spec = importlib.util.find_spec(adapter.framework_module)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            warnings.warn(
                f"skipping adapter {adapter.name!r}: framework module "
                f"{adapter.framework_module!r} is not importable",
                RuntimeWarning,
                stacklevel=3,
            )
            return
        try:
            state = adapter.apply(client)
        except ImportError as e:
            # Symmetric with the find_spec skip: if the adapter's internal
            # imports fail during apply (broken submodule, missing transitive
            # dep), treat it the same as the parent not being importable.
            warnings.warn(
                f"skipping adapter {adapter.name!r}: apply() raised ImportError: {e}",
                RuntimeWarning,
                stacklevel=3,
            )
            return
        self._entries[adapter.name] = (adapter, state)

    def unpatch_all(self) -> None:
        """Unwind stored adapters in LIFO order and close the client."""
        for adapter, state in reversed(list(self._entries.values())):
            adapter.unpatch(state)
        self._entries.clear()
        if self._client is not None:
            self._client.close()
        self._client = None

    def is_installed(self) -> bool:
        """Return True iff any adapters are currently applied."""
        return bool(self._entries)

    @property
    def client(self) -> SidecarClient | None:
        """Return the client passed to the most recent `apply`, if any."""
        return self._client


_REGISTRY = AdapterRegistry()


def apply_patches(client: SidecarClient) -> None:
    """Install the default adapter set. Idempotent per identical client."""
    if _REGISTRY.is_installed():
        if _REGISTRY.client is client:
            return
        raise RuntimeError(
            "Qortara patches already installed with a different client. "
            "Call qortara_governance.unpatch_all() first."
        )
    _REGISTRY.apply(client, _default_adapters())


def unpatch_all() -> None:
    """Restore byte-identical originals. Required for test teardown."""
    _REGISTRY.unpatch_all()


def is_patched() -> bool:
    """Return True iff patches are currently applied."""
    return _REGISTRY.is_installed()


def get_client() -> SidecarClient | None:
    """Return the currently-installed client, or None."""
    return _REGISTRY.client
