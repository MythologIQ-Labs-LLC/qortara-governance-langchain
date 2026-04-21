"""#73 REGRESSION TEST — native tool-calling path must respect policy deny.

This is the load-bearing test that makes qortara-governance-langchain
more than a prettier AGT wrapper. AGT's langchain-agentmesh hooks at the
callback level; a denial via callback is advisory and can be bypassed by
routes that skip callbacks. Our patches hook at BaseTool.invoke directly,
so ANY path that reaches tool.invoke() — including native tool-calling
through AgentExecutor — is governed.

What this test exercises:
1. Patches apply at the BaseTool class level (not per-instance wrappers).
2. Calling tool.invoke() directly (the code path native tool-calling uses
   to execute resolved tools) is intercepted.
3. On deny, the inner _run is never reached, even though we bypassed any
   callback manager in the calling code path.

This test FAILING would mean the #73 gap is open. It PASSING proves the
core value of the package.
"""
from __future__ import annotations

import pytest
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

from qortara_governance.exceptions import QortaraPolicyDenied
from qortara_governance.patches.tool_patches import apply as tool_apply
from qortara_governance.patches.tool_patches import unpatch as tool_unpatch
from qortara_protocol import DecisionKind


class DangerousTool(BaseTool):
    name: str = "dangerous_tool"
    description: str = "a tool that should be blocked"
    _side_effect_happened: bool = PrivateAttr(default=False)

    def _run(self, action: str) -> str:  # type: ignore[override]
        # Simulates a dangerous side effect (file write, API call, etc.)
        self._side_effect_happened = True
        return f"SIDE EFFECT: {action}"


def _simulate_native_tool_calling_path(tool: BaseTool, tool_input: str) -> str:
    """Simulates AgentExecutor's native tool-calling dispatch.

    In a real LangChain agent, after the LLM returns a tool_calls response,
    the executor looks up the tool by name and calls .invoke(). Crucially,
    this path does NOT go through callback.on_tool_start/end; it just
    resolves and invokes. That's the gap AGT's callback-level wrapper
    leaves open.

    We reproduce the essential call shape here: direct tool.invoke(input).
    """
    return tool.invoke(tool_input)


def test_native_tool_calling_deny_blocks_side_effect(fake_client, ctx) -> None:  # noqa: ANN001
    fake_client.scripted_decisions = [DecisionKind.DENY]
    originals = tool_apply(fake_client)
    try:
        tool = DangerousTool()
        # This is the call shape AgentExecutor uses on the native tool-calling path.
        with pytest.raises(QortaraPolicyDenied):
            _simulate_native_tool_calling_path(tool, "delete_production_database")

        # THE KEY INVARIANT: _run never reached; side effect never happened.
        assert tool._side_effect_happened is False, (
            "#73 REGRESSION: tool._run executed despite deny decision. "
            "Patches failed to intercept native tool-calling path."
        )
    finally:
        tool_unpatch(originals)


def test_patches_applied_at_class_level_not_instance(fake_client, ctx) -> None:  # noqa: ANN001
    """Patches must apply at BaseTool.invoke (class attr), not per-instance.

    If patches are per-instance, tools created AFTER init() would bypass them.
    We install patches, then construct a tool, and verify it's governed.
    """
    fake_client.scripted_decisions = [DecisionKind.DENY]
    originals = tool_apply(fake_client)
    try:
        # Construct tool AFTER patch install.
        tool = DangerousTool()
        with pytest.raises(QortaraPolicyDenied):
            tool.invoke("test")
    finally:
        tool_unpatch(originals)
