"""init() applies both default adapters when available; skips missing ones cleanly."""

from __future__ import annotations

import pytest

import qortara_governance
from qortara_governance.client import SidecarClient
from qortara_governance.patches import is_patched
from qortara_governance.patches.registry import _REGISTRY


@pytest.fixture(autouse=True)
def _teardown() -> None:
    yield
    qortara_governance.unpatch_all()


def _fake_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    # `__init__.py` binds `launch` via `from .launcher import launch`, so
    # patching `qortara_governance.launcher.launch` after import won't rebind
    # the reference in qortara_governance.__dict__. Set the sidecar endpoint
    # via env so launch() takes the existing-endpoint fast path without
    # calling `shutil.which("qortara-governance-sidecar")` — which fails in
    # environments (like public CI) where the sidecar isn't installed.
    monkeypatch.setenv("QORTARA_SIDECAR_ENDPOINT", "http://127.0.0.1:9999")
    monkeypatch.setattr(SidecarClient, "require_reachable", lambda self: None)


def _langgraph_installed() -> bool:
    try:
        import langgraph.prebuilt  # noqa: F401

        return True
    except ImportError:
        return False


def test_init_applies_both_default_adapters_when_langgraph_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_launch(monkeypatch)
    qortara_governance.init(tenant_key="tk-x")
    assert is_patched()
    applied = set(_REGISTRY._entries.keys())
    expected: set[str] = {"langchain-basetool"}
    if _langgraph_installed():
        expected.add("langgraph-toolnode")
    assert applied == expected
