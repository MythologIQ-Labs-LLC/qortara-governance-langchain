# Example code. Not production-ready.
# Shows qortara-governance-langchain intercepting a tool call in an AgentExecutor.

from __future__ import annotations

import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI  # replace with your LLM of choice

import qortara_governance
from qortara_governance import QortaraApprovalRequired, QortaraPolicyDenied


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to the given address."""
    # In a real integration this would call your mail provider.
    return f"sent to {to}"


def main() -> None:
    qortara_governance.init(tenant_key=os.environ["QORTARA_TENANT_KEY"])

    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(llm, [send_email], prompt)
    executor = AgentExecutor(agent=agent, tools=[send_email])

    try:
        result = executor.invoke(
            {"input": "Email alice@example.com with subject 'hello' and body 'hi there'."}
        )
        print("result:", result["output"])
    except QortaraPolicyDenied as denied:
        print(f"blocked by policy {denied.policy_pack_id}: {denied.rationale}")
    except QortaraApprovalRequired as needs_approval:
        print(f"approval needed at: {needs_approval.approval_url}")


if __name__ == "__main__":
    main()
