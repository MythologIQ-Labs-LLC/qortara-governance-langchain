"""tool_patches.apply refuses to double-install on already-wrapped BaseTool."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.tools import BaseTool

from qortara_governance.patches.tool_patches import apply as tool_apply
from qortara_governance.patches.tool_patches import unpatch as tool_unpatch


def test_double_install_raises_runtime_error(fake_client: Any) -> None:
    """Second apply() without unpatch must raise RuntimeError."""
    originals = tool_apply(fake_client)
    try:
        assert getattr(BaseTool.invoke, "__qortara_wrapped__", False) is True
        with pytest.raises(RuntimeError, match="already wrapped"):
            tool_apply(fake_client)
    finally:
        tool_unpatch(originals)


def test_unpatch_after_failed_double_install_restores_cleanly(
    fake_client: Any,
) -> None:
    """After a rejected double-install, original unpatch still restores state."""
    originals = tool_apply(fake_client)
    with pytest.raises(RuntimeError, match="already wrapped"):
        tool_apply(fake_client)

    tool_unpatch(originals)
    assert getattr(BaseTool.invoke, "__qortara_wrapped__", False) is False
    assert getattr(BaseTool.ainvoke, "__qortara_wrapped__", False) is False
    # And a fresh install should now succeed
    originals2 = tool_apply(fake_client)
    try:
        assert getattr(BaseTool.invoke, "__qortara_wrapped__", False) is True
    finally:
        tool_unpatch(originals2)
