"""Adapter state + version constants for the framework-adapter contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

CONTRACT_VERSION: str = "0.1"


class IncompatibleAdapterVersion(RuntimeError):
    """Raised when an adapter reports a contract_version the registry cannot honor."""


@dataclass(frozen=True)
class AdapterState:
    """Opaque handle returned by adapter.apply() and consumed by adapter.unpatch().

    `originals` maps framework-internal keys (e.g. method names) to the
    pre-patch objects. Adapters are expected to pass a read-only mapping; the
    dataclass is frozen so the registry cannot mutate it after the fact.
    """

    adapter_name: str
    originals: Mapping[str, Any]
