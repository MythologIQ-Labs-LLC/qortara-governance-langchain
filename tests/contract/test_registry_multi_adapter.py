"""AdapterRegistry applies adapters in order; unpatch_all unwinds LIFO."""

from __future__ import annotations

from types import MappingProxyType

from qortara_governance.contract import AdapterState
from qortara_governance.contract.state import CONTRACT_VERSION
from qortara_governance.patches.registry import AdapterRegistry


class _RecordingAdapter:
    def __init__(self, name: str, log: list[tuple[str, str]]) -> None:
        self.name = name
        self.framework_module = "builtins"
        self.contract_version = CONTRACT_VERSION
        self._log = log
        self._sentinel = object()

    def apply(self, client):  # noqa: ANN001, ANN201
        self._log.append(("apply", self.name))
        return AdapterState(
            adapter_name=self.name,
            originals=MappingProxyType({"sentinel": self._sentinel}),
        )

    def unpatch(self, state):  # noqa: ANN001, ANN201
        self._log.append(("unpatch", self.name))


def test_two_adapters_apply_in_order_unpatch_lifo(fake_client) -> None:  # noqa: ANN001
    log: list[tuple[str, str]] = []
    registry = AdapterRegistry()
    a = _RecordingAdapter("alpha", log)
    b = _RecordingAdapter("beta", log)
    registry.apply(fake_client, [a, b])
    assert log == [("apply", "alpha"), ("apply", "beta")]
    registry.unpatch_all()
    assert log == [
        ("apply", "alpha"),
        ("apply", "beta"),
        ("unpatch", "beta"),
        ("unpatch", "alpha"),
    ]


def test_registry_is_empty_after_unpatch(fake_client) -> None:  # noqa: ANN001
    log: list[tuple[str, str]] = []
    registry = AdapterRegistry()
    registry.apply(fake_client, [_RecordingAdapter("one", log)])
    assert registry.is_installed()
    registry.unpatch_all()
    assert not registry.is_installed()
