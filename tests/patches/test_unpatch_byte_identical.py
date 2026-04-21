"""After unpatch_all(): BaseTool.invoke is byte-identical to pre-patch."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from qortara_governance.patches.tool_patches import apply as tool_apply
from qortara_governance.patches.tool_patches import unpatch as tool_unpatch


def test_unpatch_restores_original_method_object(fake_client) -> None:  # noqa: ANN001
    original_invoke = BaseTool.invoke
    original_ainvoke = BaseTool.ainvoke

    originals = tool_apply(fake_client)

    # While patched, methods differ from originals.
    assert BaseTool.invoke is not original_invoke
    assert getattr(BaseTool.invoke, "__qortara_wrapped__", False) is True

    tool_unpatch(originals)

    # After unpatch, method objects must be byte-identical to originals.
    assert BaseTool.invoke is original_invoke
    assert BaseTool.ainvoke is original_ainvoke
    assert not getattr(BaseTool.invoke, "__qortara_wrapped__", False)
