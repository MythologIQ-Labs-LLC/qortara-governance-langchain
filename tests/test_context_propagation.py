"""Context vars propagate through nested sync + async boundaries."""

from __future__ import annotations

import asyncio

from qortara_governance.context import AgentContext, get_context, set_context


def test_set_get_simple() -> None:
    ctx = AgentContext(tenant_id="t", agent_id="a", session_id="s")
    set_context(ctx)
    assert get_context() == ctx


def test_nested_sync_sees_parent_context() -> None:
    parent = AgentContext(tenant_id="t", agent_id="a", session_id="s")
    set_context(parent)

    def inner() -> AgentContext | None:
        return get_context()

    assert inner() == parent


def test_async_task_inherits_context() -> None:
    parent = AgentContext(tenant_id="t", agent_id="a", session_id="s")

    async def worker() -> AgentContext | None:
        return get_context()

    async def runner() -> AgentContext | None:
        set_context(parent)
        return await worker()

    result = asyncio.run(runner())
    assert result == parent
