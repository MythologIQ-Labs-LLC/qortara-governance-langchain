"""Decision deny => QortaraPolicyDenied raised; inner tool never called."""
from __future__ import annotations

import pytest
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

from qortara_governance.exceptions import QortaraPolicyDenied
from qortara_governance.patches.tool_patches import apply as tool_apply
from qortara_governance.patches.tool_patches import unpatch as tool_unpatch
from qortara_protocol import DecisionKind


class ShellTool(BaseTool):
    name: str = "shell"
    description: str = "shell execution"
    _was_called: bool = PrivateAttr(default=False)

    def _run(self, cmd: str) -> str:  # type: ignore[override]
        self._was_called = True
        return f"ran: {cmd}"


def test_deny_raises_and_inner_not_called(fake_client, ctx) -> None:  # noqa: ANN001
    fake_client.scripted_decisions = [DecisionKind.DENY]
    originals = tool_apply(fake_client)
    try:
        tool = ShellTool()
        with pytest.raises(QortaraPolicyDenied) as exc_info:
            tool.invoke("rm -rf /")
        assert "fake decision: deny" in exc_info.value.rationale
        assert tool._was_called is False  # Critical invariant
    finally:
        tool_unpatch(originals)
