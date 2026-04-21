# Examples

Runnable minimal examples.

Each script is self-contained and assumes `qortara-governance-langchain` is installed:

```bash
pip install qortara-governance-langchain
# Or, for the LangGraph example:
pip install 'qortara-governance-langchain[langgraph]'
```

Set a tenant key before running:

```bash
export QORTARA_TENANT_KEY=qt_...
```

| File | What it shows |
|---|---|
| `01_basic_langchain.py` | Minimal `AgentExecutor` with a tool that gets denied by policy |
| `02_langgraph.py` | `ToolNode` path — the native-tool-calling route that requires deep patching |
| `policies/example.cedar` | An illustrative policy pack fragment |

> These are example snippets intended to demonstrate SDK integration. They are not production-ready. Adapt to your own architecture, add error handling, and review for your own data-handling requirements before any real deployment.
