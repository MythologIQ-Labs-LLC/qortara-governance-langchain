"""Context propagation via contextvars — thread-safe and async-safe."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentContext:
    """Per-agent context flowing through tool-dispatch patches."""

    tenant_id: str
    agent_id: str
    session_id: str
    workflow_id: str | None = None


_ctx_var: ContextVar[AgentContext | None] = ContextVar(
    "qortara_agent_ctx", default=None
)


def set_context(ctx: AgentContext) -> None:
    """Set the current agent context (thread + task local)."""
    _ctx_var.set(ctx)


def get_context() -> AgentContext | None:
    """Return current context, or None if no agent is active."""
    return _ctx_var.get()


def require_context() -> AgentContext:
    """Return current context or raise if not set."""
    ctx = _ctx_var.get()
    if ctx is None:
        raise RuntimeError(
            "Qortara agent context not set. Call qortara_governance.init() "
            "and ensure the current code path runs inside a governed agent."
        )
    return ctx
