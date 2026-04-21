# Example code. Not production-ready.
# Shows qortara-governance-langchain intercepting a ToolNode dispatch in LangGraph.
# Requires: pip install 'qortara-governance-langchain[langgraph]'

from __future__ import annotations

import os

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

import qortara_governance
from qortara_governance import QortaraPolicyDenied


@tool
def lookup_customer(customer_id: str) -> str:
    """Return the customer record for the given id."""
    return f"customer({customer_id})"


def build_graph():
    tools = [lookup_customer]
    llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)

    def call_model(state):
        return {"messages": [llm.invoke(state["messages"])]}

    def should_continue(state):
        last = state["messages"][-1]
        return "tools" if last.tool_calls else END

    graph = StateGraph(dict)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def main() -> None:
    qortara_governance.init(tenant_key=os.environ["QORTARA_TENANT_KEY"])

    app = build_graph()

    try:
        for event in app.stream({"messages": [HumanMessage("look up customer 42")]}):
            print(event)
    except QortaraPolicyDenied as denied:
        print(f"blocked by policy {denied.policy_pack_id}: {denied.rationale}")


if __name__ == "__main__":
    main()
