"""Adapter whose framework_module is not importable is skipped with RuntimeWarning."""

from __future__ import annotations

import warnings

from qortara_governance.contract.state import CONTRACT_VERSION
from qortara_governance.patches.registry import AdapterRegistry


class _MissingFrameworkAdapter:
    name = "ghost"
    framework_module = "definitely_not_a_module_xyz"
    contract_version = CONTRACT_VERSION

    def apply(self, client):  # noqa: ANN001, ANN201
        raise AssertionError("apply() must not be called when framework missing")

    def unpatch(self, state):  # noqa: ANN001, ANN201
        raise AssertionError("unpatch() must not be called when framework missing")


def test_registry_skips_unimportable_framework_module(fake_client) -> None:  # noqa: ANN001
    registry = AdapterRegistry()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        registry.apply(fake_client, [_MissingFrameworkAdapter()])
    messages = [
        str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)
    ]
    assert any("ghost" in m for m in messages), messages
    assert not registry.is_installed()
