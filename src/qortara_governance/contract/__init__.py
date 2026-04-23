"""Public framework-adapter contract.

Re-exports:
    FrameworkAdapter  — structural protocol every adapter implements.
    AdapterState      — frozen value returned by apply(), consumed by unpatch().
    CONTRACT_VERSION  — the contract version this SDK understands.

`ConformanceSuite` is intentionally NOT re-exported here; it remains test
infrastructure importable via `qortara_governance.contract.conformance` until
a future phase commits it as public API surface.
"""

from __future__ import annotations

from qortara_governance.contract.protocol import FrameworkAdapter
from qortara_governance.contract.state import (
    CONTRACT_VERSION,
    AdapterState,
    IncompatibleAdapterVersion,
)

__all__ = [
    "CONTRACT_VERSION",
    "AdapterState",
    "FrameworkAdapter",
    "IncompatibleAdapterVersion",
]
