"""Shared test fixtures — FakeLangChain harness + FakeSidecar."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from qortara_governance.client import SidecarClient
from qortara_governance.context import AgentContext, set_context
from qortara_protocol import ActionDecision, ActionRequest, DecisionKind, EvidenceRecord


@dataclass
class FakeClient(SidecarClient):  # type: ignore[misc]
    """SidecarClient replacement — no HTTP. Scripted decisions + decision log."""

    endpoint: str = "fake"
    tenant_key: str | None = None
    scripted_decisions: list[DecisionKind] = field(default_factory=list)
    decisions: list[ActionDecision] = field(default_factory=list)
    requests: list[ActionRequest] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    reachable: bool = True

    def __init__(self, *, scripted: list[DecisionKind] | None = None, reachable: bool = True) -> None:
        self.scripted_decisions = list(scripted) if scripted else []
        self.decisions = []
        self.requests = []
        self.evidence = []
        self.reachable = reachable

    def close(self) -> None:
        pass

    def decide(self, request: ActionRequest) -> ActionDecision:  # type: ignore[override]
        self.requests.append(request)
        kind = self.scripted_decisions.pop(0) if self.scripted_decisions else DecisionKind.ALLOW
        decision = ActionDecision(
            decision_kind=kind,
            policy_version_sha256="f" * 64,
            rationale=f"fake decision: {kind.value}",
            policy_pack_id="test-pack",
            ts=time.time(),
        )
        self.decisions.append(decision)
        return decision

    def submit_evidence(self, records: list[EvidenceRecord]) -> None:  # type: ignore[override]
        self.evidence.extend(records)

    def health(self) -> bool:  # type: ignore[override]
        return self.reachable

    def require_reachable(self) -> None:  # type: ignore[override]
        if not self.reachable:
            from qortara_governance.exceptions import QortaraSidecarUnavailable

            raise QortaraSidecarUnavailable("fake sidecar unreachable")


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def ctx() -> AgentContext:
    c = AgentContext(
        tenant_id="t-test",
        agent_id="a-test",
        session_id="s-test",
        workflow_id="w-test",
    )
    set_context(c)
    return c


@pytest.fixture(autouse=True)
def _unpatch_after(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Auto-unpatch between tests to keep state isolated."""
    yield
    from qortara_governance.patches import unpatch_all

    unpatch_all()


class FakeTool:
    """Minimal FakeLangChain tool — impersonates BaseTool interface we patch."""

    name: str = "fake_tool"

    def invoke(self, input: Any, config: Any = None) -> str:
        return f"executed: {input}"

    async def ainvoke(self, input: Any, config: Any = None) -> str:
        return f"executed_async: {input}"


@pytest.fixture
def fake_tool_cls() -> type:
    return FakeTool
