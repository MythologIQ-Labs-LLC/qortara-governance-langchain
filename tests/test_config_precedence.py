"""Config: env > kwarg > default precedence."""
from __future__ import annotations

import pytest

from qortara_governance.config import PolicyMode, load_config


def test_defaults_when_no_env_no_kwarg(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in [
        "QORTARA_SIDECAR_ENDPOINT",
        "QORTARA_TENANT_KEY",
        "QORTARA_POLICY_MODE",
        "QORTARA_OFFLINE_POLICY",
    ]:
        monkeypatch.delenv(var, raising=False)
    cfg = load_config()
    assert cfg.sidecar_endpoint is None
    assert cfg.tenant_key is None
    assert cfg.policy_mode == PolicyMode.ENFORCE
    assert cfg.offline_policy_path is None


def test_env_populates_when_no_kwarg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QORTARA_SIDECAR_ENDPOINT", "http://from-env:9000")
    monkeypatch.setenv("QORTARA_TENANT_KEY", "from-env-key")
    monkeypatch.setenv("QORTARA_POLICY_MODE", "observe")
    cfg = load_config()
    assert cfg.sidecar_endpoint == "http://from-env:9000"
    assert cfg.tenant_key == "from-env-key"
    assert cfg.policy_mode == PolicyMode.OBSERVE


def test_kwarg_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QORTARA_SIDECAR_ENDPOINT", "http://env:9000")
    cfg = load_config(sidecar_endpoint="http://kwarg:8000")
    assert cfg.sidecar_endpoint == "http://kwarg:8000"


def test_invalid_policy_mode_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QORTARA_POLICY_MODE", "not-a-mode")
    with pytest.raises(ValueError):
        load_config()


def test_invalid_policy_mode_kwarg_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QORTARA_POLICY_MODE", raising=False)
    with pytest.raises(ValueError):
        load_config(policy_mode="halfway")
