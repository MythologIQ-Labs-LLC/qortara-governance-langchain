"""Pure-function ActionRequest builders for LangChain + LangGraph dispatch.

No side effects. No imports from patch/client modules. Only depends on
qortara_protocol + context module. Keeps complexity isolated for testing.
"""

from __future__ import annotations

import time
from typing import Any

from qortara_governance.context import AgentContext
from qortara_governance.otel import current_trace_context
from qortara_protocol import ActionRequest, ActionType, Framework, RiskTier


def _guess_risk_tier(tool_name: str) -> RiskTier:
    """Conservative default: HIGH for known-dangerous tools; MEDIUM otherwise.

    The sidecar Cedar PDP is the authoritative risk evaluator; this hint
    just bumps escalation priority for obviously-dangerous tools.
    """
    high_risk = {
        "shell",
        "terminal",
        "python_repl",
        "sql",
        "filesystem",
        "shelltool",
        "bashtool",
    }
    lower = tool_name.lower()
    for keyword in high_risk:
        if keyword in lower:
            return RiskTier.HIGH
    return RiskTier.MEDIUM


def build_tool_action(
    tool_name: str,
    tool_input: Any,
    ctx: AgentContext,
) -> ActionRequest:
    """Build an ActionRequest for a BaseTool.invoke dispatch."""
    del tool_input  # payload is NOT inlined; sidecar gets a reference if needed later.
    return ActionRequest(
        tenant_id=ctx.tenant_id,
        agent_id=ctx.agent_id,
        session_id=ctx.session_id,
        workflow_id=ctx.workflow_id,
        framework=Framework.LANGCHAIN,
        action_type=ActionType.TOOL_DISPATCH,
        target_resource=tool_name,
        requested_capability=f"tool:{tool_name}",
        risk_tier=_guess_risk_tier(tool_name),
        ts=time.time(),
        trace_context=current_trace_context(),
    )


def build_toolnode_action(
    tool_name: str,
    ctx: AgentContext,
) -> ActionRequest:
    """Build an ActionRequest for a LangGraph ToolNode dispatch."""
    return ActionRequest(
        tenant_id=ctx.tenant_id,
        agent_id=ctx.agent_id,
        session_id=ctx.session_id,
        workflow_id=ctx.workflow_id,
        framework=Framework.LANGGRAPH,
        action_type=ActionType.TOOL_DISPATCH,
        target_resource=tool_name,
        requested_capability=f"tool:{tool_name}",
        risk_tier=_guess_risk_tier(tool_name),
        ts=time.time(),
        trace_context=current_trace_context(),
    )
