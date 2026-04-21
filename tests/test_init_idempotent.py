"""init() called twice with same args => no-op; different args => RuntimeError."""

from __future__ import annotations

import pytest

import qortara_governance
from qortara_governance.client import SidecarClient
from qortara_governance.patches import is_patched


@pytest.fixture(autouse=True)
def _teardown() -> None:
    yield
    qortara_governance.unpatch_all()


def _fake_launch(
    monkeypatch: pytest.MonkeyPatch, endpoint: str = "http://127.0.0.1:9999"
) -> None:
    """Monkeypatch launcher + client health to avoid real subprocess + HTTP."""
    from qortara_governance import launcher

    class _LaunchResult:
        def __init__(self, ep: str) -> None:
            self.endpoint = ep
            self.spawned = False
            self.process = None

    monkeypatch.setattr(
        launcher,
        "launch",
        lambda *, existing_endpoint: _LaunchResult(existing_endpoint or endpoint),
    )
    monkeypatch.setattr(SidecarClient, "require_reachable", lambda self: None)


def test_init_twice_same_args_is_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_launch(monkeypatch)
    qortara_governance.init(tenant_key="k1", sidecar_endpoint="http://127.0.0.1:9999")
    assert is_patched()
    # Second identical call must not raise.
    qortara_governance.init(tenant_key="k1", sidecar_endpoint="http://127.0.0.1:9999")


def test_init_twice_different_args_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_launch(monkeypatch)
    qortara_governance.init(tenant_key="k1", sidecar_endpoint="http://127.0.0.1:9999")
    with pytest.raises(RuntimeError):
        qortara_governance.init(
            tenant_key="k2", sidecar_endpoint="http://127.0.0.1:9999"
        )


def test_unpatch_all_allows_reinit(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_launch(monkeypatch)
    qortara_governance.init(tenant_key="k1", sidecar_endpoint="http://127.0.0.1:9999")
    qortara_governance.unpatch_all()
    assert not is_patched()
    # Now re-init with different args must succeed.
    qortara_governance.init(tenant_key="k2", sidecar_endpoint="http://127.0.0.1:9998")
    assert is_patched()
