"""BaseTool.invoke / .ainvoke patches — deep-hook tool-dispatch interception.

Closes AGT issue #73: callback-level wrappers observe tool calls but don't
reliably block native tool-calling dispatch. This module patches the actual
invoke methods on BaseTool so every dispatch path flows through policy.

Exports:
    apply() -> originals  # install patches; returns originals for unpatch
    unpatch(originals)    # restore byte-identical originals
"""

from __future__ import annotations

from typing import Any, Callable

from qortara_governance.client import SidecarClient
from qortara_governance.context import get_context
from qortara_governance.decorators import is_exempt
from qortara_governance.exceptions import QortaraApprovalRequired, QortaraPolicyDenied
from qortara_governance.patches.action_builder import build_tool_action
from qortara_protocol import DecisionKind

_OriginalMethod = Callable[..., Any]


def _decide_or_raise(tool: object, tool_input: Any, client: SidecarClient) -> None:
    """Request a decision; raise on deny/require_approval; return on allow/exempt."""
    if is_exempt(tool):
        return
    ctx = get_context()
    if ctx is None:
        # No agent context = not governed; pass through.
        return
    tool_name = getattr(tool, "name", type(tool).__name__)
    request = build_tool_action(tool_name, tool_input, ctx)
    decision = client.decide(request)
    if decision.decision_kind == DecisionKind.DENY:
        raise QortaraPolicyDenied(
            rationale=decision.rationale,
            policy_pack_id=decision.policy_pack_id,
            policy_version_sha256=decision.policy_version_sha256,
        )
    if decision.decision_kind == DecisionKind.REQUIRE_APPROVAL:
        raise QortaraApprovalRequired(
            rationale=decision.rationale,
            approval_url=decision.approval_url,
            policy_pack_id=decision.policy_pack_id,
        )


def _make_sync_wrapper(
    original: _OriginalMethod, client: SidecarClient
) -> _OriginalMethod:
    def wrapper(self: object, input: Any, config: Any = None, **kwargs: Any) -> Any:
        _decide_or_raise(self, input, client)
        return original(self, input, config, **kwargs)

    wrapper.__qualname__ = original.__qualname__
    wrapper.__qortara_wrapped__ = True  # type: ignore[attr-defined]
    wrapper.__qortara_original__ = original  # type: ignore[attr-defined]
    return wrapper


def _make_async_wrapper(
    original: _OriginalMethod, client: SidecarClient
) -> _OriginalMethod:
    async def wrapper(
        self: object, input: Any, config: Any = None, **kwargs: Any
    ) -> Any:
        _decide_or_raise(self, input, client)
        return await original(self, input, config, **kwargs)

    wrapper.__qualname__ = original.__qualname__
    wrapper.__qortara_wrapped__ = True  # type: ignore[attr-defined]
    wrapper.__qortara_original__ = original  # type: ignore[attr-defined]
    return wrapper


def apply(client: SidecarClient) -> dict[str, _OriginalMethod]:
    """Install BaseTool.invoke/ainvoke patches. Returns originals for unpatch."""
    from langchain_core.tools import BaseTool

    originals: dict[str, _OriginalMethod] = {
        "invoke": BaseTool.invoke,
        "ainvoke": BaseTool.ainvoke,
    }
    BaseTool.invoke = _make_sync_wrapper(BaseTool.invoke, client)  # type: ignore[method-assign]
    BaseTool.ainvoke = _make_async_wrapper(BaseTool.ainvoke, client)  # type: ignore[method-assign]
    return originals


def unpatch(originals: dict[str, _OriginalMethod]) -> None:
    """Restore BaseTool.invoke/ainvoke to byte-identical originals."""
    from langchain_core.tools import BaseTool

    BaseTool.invoke = originals["invoke"]  # type: ignore[method-assign]
    BaseTool.ainvoke = originals["ainvoke"]  # type: ignore[method-assign]
