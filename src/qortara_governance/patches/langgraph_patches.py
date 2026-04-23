"""LangGraph ToolNode.invoke patches — optional (silent skip if langgraph absent)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Callable

from qortara_governance.client import SidecarClient
from qortara_governance.context import get_context
from qortara_governance.contract.state import CONTRACT_VERSION, AdapterState
from qortara_governance.exceptions import QortaraApprovalRequired, QortaraPolicyDenied
from qortara_governance.patches.action_builder import build_toolnode_action
from qortara_protocol import DecisionKind

_OriginalMethod = Callable[..., Any]


def _langgraph_available() -> bool:
    try:
        import langgraph.prebuilt  # noqa: F401

        return True
    except ImportError:
        return False


def _extract_tool_names(state: Any) -> list[str]:
    """Best-effort extraction of tool names from a ToolNode invocation state.

    LangGraph passes state with a `messages` list containing the last AI message,
    which may have `tool_calls`. Returns tool names for pre-decision policy check.
    Falls back to ["<unknown>"] if structure doesn't match.
    """
    try:
        messages = (
            state.get("messages", [])
            if isinstance(state, dict)
            else getattr(state, "messages", [])
        )
        if not messages:
            return ["<unknown>"]
        last = messages[-1]
        tool_calls = getattr(last, "tool_calls", None) or (
            last.get("tool_calls") if isinstance(last, dict) else None
        )
        if not tool_calls:
            return ["<unknown>"]
        return [
            tc.get("name", "<unknown>")
            if isinstance(tc, dict)
            else getattr(tc, "name", "<unknown>")
            for tc in tool_calls
        ]
    except (AttributeError, TypeError, KeyError):
        return ["<unknown>"]


def _decide_each(tool_names: list[str], client: SidecarClient) -> None:
    ctx = get_context()
    if ctx is None:
        return
    for name in tool_names:
        decision = client.decide(build_toolnode_action(name, ctx))
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


def _make_wrapper(original: _OriginalMethod, client: SidecarClient) -> _OriginalMethod:
    def wrapper(self: object, input: Any, config: Any = None, **kwargs: Any) -> Any:
        _decide_each(_extract_tool_names(input), client)
        return original(self, input, config, **kwargs)

    wrapper.__qualname__ = original.__qualname__
    wrapper.__qortara_wrapped__ = True  # type: ignore[attr-defined]
    wrapper.__qortara_original__ = original  # type: ignore[attr-defined]
    return wrapper


def apply(client: SidecarClient) -> dict[str, _OriginalMethod] | None:
    """Install ToolNode.invoke patch if langgraph available; else silent skip."""
    if not _langgraph_available():
        return None
    from langgraph.prebuilt import ToolNode

    if getattr(ToolNode.invoke, "__qortara_wrapped__", False):
        raise RuntimeError(
            "ToolNode.invoke is already wrapped by Qortara - refusing to "
            "double-install. Call langgraph_patches.unpatch(originals) before "
            "re-installing."
        )
    originals: dict[str, _OriginalMethod] = {"invoke": ToolNode.invoke}
    ToolNode.invoke = _make_wrapper(ToolNode.invoke, client)  # type: ignore[method-assign]
    return originals


def unpatch(originals: dict[str, _OriginalMethod] | None) -> None:
    """Restore ToolNode.invoke. No-op if originals is None (langgraph absent)."""
    if originals is None:
        return
    from langgraph.prebuilt import ToolNode

    ToolNode.invoke = originals["invoke"]  # type: ignore[method-assign]


class LangGraphToolNodeAdapter:
    """FrameworkAdapter wrapping langgraph.prebuilt.ToolNode.invoke patches."""

    name: str = "langgraph-toolnode"
    framework_module: str = "langgraph.prebuilt"
    contract_version: str = CONTRACT_VERSION

    def apply(self, client: SidecarClient) -> AdapterState:
        """Install the ToolNode patch and return an AdapterState.

        Raises ImportError when langgraph is not installed; the registry is
        expected to probe `framework_module` importability and skip the
        adapter before calling apply.
        """
        originals = apply(client)
        if originals is None:
            raise ImportError(
                "langgraph is not installed; LangGraphToolNodeAdapter.apply() "
                "requires the optional [langgraph] extra"
            )
        return AdapterState(
            adapter_name=self.name,
            originals=MappingProxyType(dict(originals)),
        )

    def unpatch(self, state: AdapterState) -> None:
        """Restore ToolNode.invoke from the snapshot in `state`."""
        unpatch(dict(state.originals))
