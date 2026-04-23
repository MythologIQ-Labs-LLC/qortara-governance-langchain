"""langgraph_patches.apply refuses to double-install on already-wrapped ToolNode."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("langgraph")

from langgraph.prebuilt import ToolNode  # noqa: E402

from qortara_governance.patches.langgraph_patches import apply as lg_apply  # noqa: E402
from qortara_governance.patches.langgraph_patches import (  # noqa: E402
    unpatch as lg_unpatch,
)


def test_langgraph_double_install_raises_runtime_error(fake_client: Any) -> None:
    """Second apply() without unpatch must raise RuntimeError."""
    originals = lg_apply(fake_client)
    try:
        assert originals is not None
        assert getattr(ToolNode.invoke, "__qortara_wrapped__", False) is True
        with pytest.raises(RuntimeError, match="already wrapped"):
            lg_apply(fake_client)
    finally:
        lg_unpatch(originals)


def test_langgraph_unpatch_after_failed_double_install(fake_client: Any) -> None:
    """After rejected double-install, original unpatch still restores state."""
    originals = lg_apply(fake_client)
    assert originals is not None
    with pytest.raises(RuntimeError, match="already wrapped"):
        lg_apply(fake_client)

    lg_unpatch(originals)
    assert getattr(ToolNode.invoke, "__qortara_wrapped__", False) is False
    # Fresh install should now succeed
    originals2 = lg_apply(fake_client)
    try:
        assert originals2 is not None
        assert getattr(ToolNode.invoke, "__qortara_wrapped__", False) is True
    finally:
        lg_unpatch(originals2)
