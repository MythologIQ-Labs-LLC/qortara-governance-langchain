"""FrameworkAdapter protocol — structural contract for patch providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from qortara_governance.client import SidecarClient
from qortara_governance.contract.state import AdapterState


@runtime_checkable
class FrameworkAdapter(Protocol):
    """Structural contract every framework adapter must satisfy.

    Implementations are stateless: `apply` monkey-patches the target framework
    and returns an `AdapterState` containing whatever originals are needed by
    `unpatch` to restore byte-identical pre-patch behavior.
    """

    name: str
    framework_module: str
    contract_version: str

    def apply(self, client: SidecarClient) -> AdapterState:
        """Install patches against the target framework; return an AdapterState."""

    def unpatch(self, state: AdapterState) -> None:
        """Restore the framework to its pre-apply state."""
