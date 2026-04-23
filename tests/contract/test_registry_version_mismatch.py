"""Adapter with contract_version != CONTRACT_VERSION is rejected."""

from __future__ import annotations

import pytest

from qortara_governance.contract import AdapterState, IncompatibleAdapterVersion
from qortara_governance.patches.registry import AdapterRegistry


class _FutureAdapter:
    name = "future"
    framework_module = "builtins"
    contract_version = "9.9"

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name=self.name, originals={})

    def unpatch(self, state):  # noqa: ANN001, ANN201
        return None


def test_registry_rejects_future_contract_version(fake_client) -> None:  # noqa: ANN001
    registry = AdapterRegistry()
    with pytest.raises(IncompatibleAdapterVersion, match="9.9"):
        registry.apply(fake_client, [_FutureAdapter()])
