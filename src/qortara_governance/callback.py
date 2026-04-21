"""QortaraCallbackHandler — additive observability (never blocks execution).

Complements the deep-hook patches by observing chain boundaries, retriever
calls, and memory operations that the patches don't intercept. Emits
EvidenceRecord with decision_kind=observe. Never raises from callback methods.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from qortara_governance.client import SidecarClient
from qortara_governance.context import get_context
from qortara_governance.otel import current_trace_context
from qortara_protocol import (
    ActionDecision,
    ActionRequest,
    ActionType,
    DecisionKind,
    EvidenceRecord,
    ExecutionResult,
    Framework,
    RiskTier,
)


def _build_observe_request(action_type: ActionType, resource: str) -> ActionRequest | None:
    ctx = get_context()
    if ctx is None:
        return None
    return ActionRequest(
        tenant_id=ctx.tenant_id,
        agent_id=ctx.agent_id,
        session_id=ctx.session_id,
        workflow_id=ctx.workflow_id,
        framework=Framework.LANGCHAIN,
        action_type=action_type,
        target_resource=resource,
        requested_capability=f"observe:{action_type.value}",
        risk_tier=RiskTier.LOW,
        ts=time.time(),
        trace_context=current_trace_context(),
    )


def _observe_decision() -> ActionDecision:
    return ActionDecision(
        decision_kind=DecisionKind.OBSERVE,
        policy_version_sha256="callback-observe",
        rationale="additive observability — no policy check",
        policy_pack_id="sdk-callback",
        ts=time.time(),
    )


class QortaraCallbackHandler(BaseCallbackHandler):
    """Callback handler emitting observe-evidence for non-tool dispatch events."""

    def __init__(self, client: SidecarClient) -> None:
        self._client = client

    def _emit(self, action_type: ActionType, resource: str) -> None:
        request = _build_observe_request(action_type, resource)
        if request is None:
            return
        ctx = get_context()
        if ctx is None:
            return
        record = EvidenceRecord(
            evidence_id=str(uuid.uuid4()),
            tenant_id=ctx.tenant_id,
            request=request,
            decision=_observe_decision(),
            execution_result=ExecutionResult.OBSERVED,
            duration_ms=0,
            ts=time.time(),
        )
        try:
            self._client.submit_evidence([record])
        except Exception:  # noqa: BLE001 — callback never blocks
            pass

    def on_chain_start(self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any) -> None:
        name = (serialized or {}).get("name", "chain")
        self._emit(ActionType.CHAIN_BOUNDARY, str(name))

    def on_retriever_start(self, serialized: dict[str, Any], query: str, **kwargs: Any) -> None:
        name = (serialized or {}).get("name", "retriever")
        self._emit(ActionType.RETRIEVAL, str(name))

    def on_retriever_error(self, error: BaseException, **kwargs: Any) -> None:
        # Error on retrieval is still an evidence-worthy event.
        self._emit(ActionType.RETRIEVAL, f"error:{type(error).__name__}")
