"""FrameworkAdapter is @runtime_checkable — isinstance() works structurally."""

from __future__ import annotations

from qortara_governance.contract import AdapterState, FrameworkAdapter
from qortara_governance.contract.state import CONTRACT_VERSION


class _CompleteAdapter:
    name = "complete"
    framework_module = "builtins"
    contract_version = CONTRACT_VERSION

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name=self.name, originals={})

    def unpatch(self, state):  # noqa: ANN001, ANN201
        return None


class _MissingUnpatch:
    name = "missing"
    framework_module = "builtins"
    contract_version = CONTRACT_VERSION

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name=self.name, originals={})


def test_complete_adapter_is_instance() -> None:
    assert isinstance(_CompleteAdapter(), FrameworkAdapter)


def test_bare_dict_is_not_instance() -> None:
    assert not isinstance({"name": "x"}, FrameworkAdapter)


def test_class_missing_method_is_not_instance() -> None:
    assert not isinstance(_MissingUnpatch(), FrameworkAdapter)
