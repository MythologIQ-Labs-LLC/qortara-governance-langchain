"""Registry probes framework availability via find_spec, not import_module.

Guarantees the availability probe is side-effect-free: a framework module's
import-time side effects (globals, network, registry mutation) must not fire
when the registry merely checks whether the adapter's framework is present.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest

from qortara_governance.contract.state import CONTRACT_VERSION, AdapterState
from qortara_governance.patches.registry import AdapterRegistry


class _ProbeOnlyAdapter:
    """Adapter whose framework_module is a real, importable stdlib module.

    `apply()` raises so the test would fail if the registry ever let it run;
    we only care about the probe step here.
    """

    name = "probe-only"
    framework_module = "json"  # stdlib — guaranteed findable
    contract_version = CONTRACT_VERSION

    def apply(self, client: Any) -> AdapterState:
        raise AssertionError("apply() must not run in this test")

    def unpatch(self, state: AdapterState) -> None:
        raise AssertionError("unpatch() must not run in this test")


def test_registry_uses_find_spec_not_import_module(
    fake_client: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AdapterRegistry probes via find_spec; import_module must not be called."""

    def _explode(name: str, package: str | None = None) -> Any:
        raise AssertionError(
            f"importlib.import_module({name!r}) must not be called during probe"
        )

    monkeypatch.setattr(importlib, "import_module", _explode)

    registry = AdapterRegistry()
    adapter = _ProbeOnlyAdapter()

    # apply() on the adapter raises AssertionError — so the probe step runs
    # first and the import_module sentinel above would also trip if touched.
    with pytest.raises(AssertionError, match="apply\\(\\) must not run"):
        registry.apply(fake_client, [adapter])


def test_registry_find_spec_handles_missing_parent_package(
    fake_client: Any,
) -> None:
    """Dotted path with missing parent raises ModuleNotFoundError — skip cleanly."""

    class _DottedMissingAdapter:
        name = "dotted-missing"
        framework_module = "definitely_absent_xyz.submodule"
        contract_version = CONTRACT_VERSION

        def apply(self, client: Any) -> AdapterState:
            raise AssertionError("apply() must not run when parent missing")

        def unpatch(self, state: AdapterState) -> None:
            raise AssertionError("unpatch() must not run when parent missing")

    registry = AdapterRegistry()

    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        registry.apply(fake_client, [_DottedMissingAdapter()])

    messages = [str(w.message) for w in caught if w.category is RuntimeWarning]
    assert any("dotted-missing" in m for m in messages), messages
    assert not registry.is_installed()
    # Ensure parent module wasn't spuriously imported
    assert "definitely_absent_xyz" not in sys.modules
