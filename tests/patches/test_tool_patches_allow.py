"""Decision allow => inner tool called with original args."""
from __future__ import annotations

from langchain_core.tools import BaseTool
from pydantic import Field

from qortara_governance.patches.tool_patches import apply as tool_apply
from qortara_governance.patches.tool_patches import unpatch as tool_unpatch
from qortara_protocol import DecisionKind


class EchoTool(BaseTool):
    name: str = "echo"
    description: str = "echo input back"
    call_count: int = Field(default=0)

    def _run(self, query: str) -> str:  # type: ignore[override]
        return f"echoed: {query}"


def test_allow_executes_tool(fake_client, ctx) -> None:  # noqa: ANN001
    fake_client.scripted_decisions = [DecisionKind.ALLOW]
    originals = tool_apply(fake_client)
    try:
        tool = EchoTool()
        result = tool.invoke("hello")
        assert result == "echoed: hello"
        assert len(fake_client.decisions) == 1
        assert fake_client.decisions[0].decision_kind == DecisionKind.ALLOW
    finally:
        tool_unpatch(originals)
