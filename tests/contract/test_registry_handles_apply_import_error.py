"""M3: AdapterRegistry skips adapters whose apply() raises ImportError.

Symmetric with the find_spec-returns-None skip: if an adapter's internal
import (e.g. a broken submodule) raises ImportError during apply(), the
registry must skip that adapter with RuntimeWarning — not propagate the
error and abort installation of subsequent adapters.
"""

from __future__ import annotations

import pytest

from qortara_governance.contract.state import CONTRACT_VERSION, AdapterState
from qortara_governance.patches.registry import AdapterRegistry


class _ApplyRaisesImportError:
    """Framework module spec exists (find_spec succeeds), but apply() raises."""

    name = "broken-submodule-adapter"
    framework_module = "sys"  # a real module so find_spec succeeds
    contract_version = CONTRACT_VERSION

    def apply(self, client: object) -> AdapterState:
        raise ImportError("simulated broken submodule: cannot import X from Y")

    def unpatch(self, state: AdapterState) -> None:
        raise AssertionError("unpatch must never be called on a skipped adapter")


class _ApplyOk:
    """Successful fallback adapter — proves subsequent adapters still apply."""

    name = "ok-adapter"
    framework_module = "sys"
    contract_version = CONTRACT_VERSION

    def __init__(self) -> None:
        self.applied = False

    def apply(self, client: object) -> AdapterState:
        self.applied = True
        return AdapterState(adapter_name=self.name, originals={})

    def unpatch(self, state: AdapterState) -> None:
        self.applied = False


def test_registry_skips_adapter_that_raises_importerror_on_apply(
    recwarn: pytest.WarningsRecorder,
) -> None:
    reg = AdapterRegistry()
    broken = _ApplyRaisesImportError()
    ok = _ApplyOk()

    reg.apply(client=object(), adapters=[broken, ok])  # type: ignore[arg-type]

    # Broken adapter skipped with RuntimeWarning; ok adapter still applied.
    warning_messages = [str(w.message) for w in recwarn.list]
    assert any(
        "broken-submodule-adapter" in m and "ImportError" in m for m in warning_messages
    ), (
        f"expected RuntimeWarning mentioning adapter + ImportError; got {warning_messages}"
    )
    assert ok.applied, "adapters after a skipped one must still apply"
    # Registry holds only the successful adapter.
    assert reg.is_installed()


def test_registry_without_broken_adapter_also_works(
    recwarn: pytest.WarningsRecorder,
) -> None:
    reg = AdapterRegistry()
    ok = _ApplyOk()
    reg.apply(client=object(), adapters=[ok])  # type: ignore[arg-type]
    assert ok.applied
    # Control: no ImportError warning in this path.
    for w in recwarn.list:
        assert "ImportError" not in str(w.message)
