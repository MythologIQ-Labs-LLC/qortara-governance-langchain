"""LangGraph ToolNode patches — applied when langgraph installed; silent skip otherwise."""
from __future__ import annotations

import pytest

from qortara_governance.patches.langgraph_patches import _langgraph_available, apply, unpatch


def test_langgraph_silent_skip_when_unavailable(monkeypatch: pytest.MonkeyPatch, fake_client) -> None:  # noqa: ANN001
    """When langgraph absent, apply() returns None and unpatch() is no-op."""
    from qortara_governance.patches import langgraph_patches

    monkeypatch.setattr(langgraph_patches, "_langgraph_available", lambda: False)
    originals = apply(fake_client)
    assert originals is None
    # unpatch(None) must not raise.
    unpatch(None)


@pytest.mark.skipif(
    not _langgraph_available(),
    reason="langgraph not installed in test env — skipping real integration",
)
def test_langgraph_patches_toolnode_when_available(fake_client) -> None:  # noqa: ANN001
    """If langgraph is present, apply() patches ToolNode.invoke."""
    from langgraph.prebuilt import ToolNode

    original = ToolNode.invoke
    originals = apply(fake_client)
    try:
        assert originals is not None
        assert ToolNode.invoke is not original
        assert getattr(ToolNode.invoke, "__qortara_wrapped__", False) is True
    finally:
        unpatch(originals)
    assert ToolNode.invoke is original
