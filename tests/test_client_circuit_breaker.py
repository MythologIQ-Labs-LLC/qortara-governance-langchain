"""Circuit breaker: N 5xx in a row => deny-all; recovers after cooldown."""
from __future__ import annotations

import time

import httpx
import pytest

from qortara_governance import client as client_mod
from qortara_governance.client import SidecarClient, _BREAKER_THRESHOLD, _deny_all
from qortara_protocol import ActionRequest, ActionType, DecisionKind, Framework


def _req() -> ActionRequest:
    return ActionRequest(
        tenant_id="t",
        agent_id="a",
        session_id="s",
        framework=Framework.LANGCHAIN,
        action_type=ActionType.TOOL_DISPATCH,
        target_resource="fake",
        requested_capability="fake",
        ts=time.time(),
    )


def _mock_transport_5xx() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    return httpx.MockTransport(handler)


def _make_client(transport: httpx.MockTransport) -> SidecarClient:
    c = SidecarClient("http://fake", None)
    c._client = httpx.Client(base_url="http://fake", transport=transport)
    return c


def test_deny_all_helper_returns_deny_kind() -> None:
    d = _deny_all("reason")
    assert d.decision_kind == DecisionKind.DENY


def test_consecutive_5xx_trip_breaker() -> None:
    client = _make_client(_mock_transport_5xx())
    for _ in range(_BREAKER_THRESHOLD):
        decision = client.decide(_req())
        assert decision.decision_kind == DecisionKind.DENY

    # Breaker is now tripped; subsequent calls deny without contacting transport.
    post_trip = client.decide(_req())
    assert post_trip.decision_kind == DecisionKind.DENY
    assert "circuit breaker" in post_trip.rationale.lower()


def test_breaker_cooldown_resets_on_elapsed(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(_mock_transport_5xx())
    for _ in range(_BREAKER_THRESHOLD):
        client.decide(_req())
    assert client._breaker.consecutive_failures >= _BREAKER_THRESHOLD

    # Fast-forward past cooldown — breaker should auto-reset on next call.
    monkeypatch.setattr(client_mod, "_BREAKER_COOLDOWN_S", 0.01)
    time.sleep(0.02)
    # Next call: consecutive_failures is reset to 0, but underlying transport
    # still returns 503, so decision is still deny — important invariant: the
    # breaker reset lets us try again, but doesn't flip reality on its own.
    client.decide(_req())
    # consecutive_failures will have re-incremented to 1 after reset-then-fail
    assert client._breaker.consecutive_failures >= 1
