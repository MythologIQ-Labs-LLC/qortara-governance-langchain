"""ConformanceSuite — reusable invariants for any FrameworkAdapter implementation.

Importable via `qortara_governance.contract.conformance`; intentionally NOT
re-exported from `qortara_governance.contract` until a future phase commits
this as public API surface.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable

from qortara_governance.client import SidecarClient
from qortara_governance.contract.protocol import FrameworkAdapter
from qortara_governance.contract.state import CONTRACT_VERSION, AdapterState


def _method_identity(obj: Any) -> Any:
    """Return a stable identity for a bound/unbound method suitable for byte-identical checks."""
    func = getattr(obj, "__func__", obj)
    return getattr(func, "__code__", func)


class ConformanceSuite:
    """Invariant suite a concrete adapter must pass to claim contract compliance."""

    def __init__(
        self,
        adapter: FrameworkAdapter,
        client_factory: Callable[[], SidecarClient],
    ) -> None:
        self.adapter = adapter
        self.client_factory = client_factory

    def test_contract_version_matches(self) -> None:
        """Adapter's declared contract_version must equal the registry's CONTRACT_VERSION."""
        assert self.adapter.contract_version == CONTRACT_VERSION, (
            f"adapter {self.adapter.name!r} contract_version="
            f"{self.adapter.contract_version!r} does not match "
            f"CONTRACT_VERSION={CONTRACT_VERSION!r}"
        )

    def test_state_roundtrip(self) -> None:
        """apply() returns an AdapterState whose adapter_name and originals are coherent."""
        # Import-gate first so we produce a clean skip signal if the framework is absent.
        importlib.import_module(self.adapter.framework_module)
        state = self.adapter.apply(self.client_factory())
        try:
            assert isinstance(state, AdapterState), (
                f"apply() must return AdapterState, got {type(state).__name__}"
            )
            assert state.adapter_name == self.adapter.name, (
                f"state.adapter_name={state.adapter_name!r} "
                f"!= adapter.name={self.adapter.name!r}"
            )
            assert len(state.originals) >= 1, (
                f"adapter {self.adapter.name!r} returned empty originals mapping"
            )
        finally:
            self.adapter.unpatch(state)

    def test_unpatch_restores_byte_identical(self) -> None:
        """apply → unpatch → re-apply must observe identical original method identities."""
        importlib.import_module(self.adapter.framework_module)
        first = self.adapter.apply(self.client_factory())
        baseline = {k: _method_identity(first.originals[k]) for k in first.originals}
        self.adapter.unpatch(first)
        second = self.adapter.apply(self.client_factory())
        try:
            for key in second.originals:
                got = _method_identity(second.originals[key])
                assert got == baseline[key], (
                    f"adapter {self.adapter.name!r} did not restore "
                    f"byte-identical {key!r}: got {got!r}, expected {baseline[key]!r}"
                )
        finally:
            self.adapter.unpatch(second)

    def test_apply_is_idempotent(self) -> None:
        """Two independent apply/unpatch cycles leave the framework in the same state.

        Adapters are stateless; the registry enforces idempotence at the
        process-singleton layer. This invariant verifies that sequential
        apply/unpatch cycles are each a clean round-trip — which is the
        property the registry relies on.
        """
        importlib.import_module(self.adapter.framework_module)
        first = self.adapter.apply(self.client_factory())
        first_ids = {k: _method_identity(first.originals[k]) for k in first.originals}
        self.adapter.unpatch(first)
        second = self.adapter.apply(self.client_factory())
        try:
            second_ids = {
                k: _method_identity(second.originals[k]) for k in second.originals
            }
            assert first_ids == second_ids, (
                f"adapter {self.adapter.name!r} originals diverged across "
                f"apply cycles: {first_ids!r} vs {second_ids!r}"
            )
        finally:
            self.adapter.unpatch(second)
