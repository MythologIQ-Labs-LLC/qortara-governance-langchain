# qortara-governance-langchain

Policy enforcement for LangChain and LangGraph agents, at the point of tool dispatch.

[![PyPI](https://img.shields.io/pypi/v/qortara-governance-langchain.svg)](https://pypi.org/project/qortara-governance-langchain/)
[![Python](https://img.shields.io/pypi/pyversions/qortara-governance-langchain.svg)](https://pypi.org/project/qortara-governance-langchain/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#status)

```python
import qortara_governance

qortara_governance.init(tenant_key="qt_...")

# Existing LangChain / LangGraph code runs unchanged.
# Tool dispatches now pass through policy evaluation before execution.
```

---

## What it does

`qortara-governance-langchain` intercepts tool dispatch inside LangChain and LangGraph agents and routes each call through a local policy decision point before execution. Denied calls raise a typed exception; allowed calls execute normally; calls requiring human approval raise with an approval URL.

Enforcement happens at `BaseTool.invoke` / `BaseTool.ainvoke` and (optionally) `langgraph.prebuilt.ToolNode.invoke` — the paths native tool-calling agents actually take, not just the callback surface that wrapper-based governance can observe.

This is a companion to LangSmith, not a replacement. LangSmith traces execution; this SDK decides whether execution is allowed to happen.

## Install

```bash
pip install qortara-governance-langchain

# Optional — LangGraph support:
pip install 'qortara-governance-langchain[langgraph]'
```

Requires Python 3.10+ and `langchain-core >= 0.3`.

## Quickstart

```python
import qortara_governance
from langchain_core.tools import tool
from langchain.agents import AgentExecutor

qortara_governance.init(tenant_key="qt_...")

@tool
def send_email(to: str, body: str) -> str:
    """Send an email."""
    ...

# agent + AgentExecutor configured as usual
agent_executor = AgentExecutor(agent=agent, tools=[send_email])

try:
    result = agent_executor.invoke({"input": "Email the finance list the Q3 numbers."})
except qortara_governance.QortaraPolicyDenied as denied:
    log.warning("blocked by policy: %s", denied.rationale)
except qortara_governance.QortaraApprovalRequired as needs_approval:
    log.info("approval needed at: %s", needs_approval.approval_url)
```

## Decision model

Every intercepted call receives one of four decisions:

| Decision | SDK behavior |
|---|---|
| `allow` | Execute the tool normally |
| `deny` | Raise `QortaraPolicyDenied` with rationale + policy identifiers |
| `require_approval` | Raise `QortaraApprovalRequired` with an approval URL |
| `exempt` | Execute without evaluation (tool marked via `@qortara_exempt`) |

```python
from qortara_governance import qortara_exempt

@qortara_exempt
@tool
def read_clock() -> str:
    """Trusted internal tool — no policy evaluation."""
    return datetime.utcnow().isoformat()
```

Exempt tools still emit evidence records so audits remain complete.

## Sidecar

The SDK talks to a local sidecar process over HTTP. Two run modes are supported:

- **Subprocess (default).** `init()` launches the sidecar as a child process, bound to `127.0.0.1` on an ephemeral port. It terminates with the parent. No configuration required.
- **Daemon.** Run the sidecar externally and set `QORTARA_SIDECAR_ENDPOINT=http://host:port`. `init()` will use the existing endpoint instead of spawning one.

If the sidecar becomes unreachable, the SDK enters a circuit-breaker state that fails closed for a short cooldown window. Calls during that window raise `QortaraSidecarUnavailable`.

## Configuration

Every option resolves in this precedence: `init()` kwarg → environment variable → default.

| Option | Env var | Default | Notes |
|---|---|---|---|
| `tenant_key` | `QORTARA_TENANT_KEY` | *(none)* | Required for hosted decisions; optional for local-only policy packs |
| `sidecar_endpoint` | `QORTARA_SIDECAR_ENDPOINT` | *(spawn subprocess)* | Set to use an external daemon |
| `policy_mode` | `QORTARA_POLICY_MODE` | `enforce` | `enforce` raises on deny; `observe` logs but executes |
| `offline_policy_path` | `QORTARA_OFFLINE_POLICY` | *(none)* | Path to a local policy pack for air-gapped environments |

## Observability

`QortaraCallbackHandler` is an additive LangChain callback for chain-boundary and retrieval events. It never blocks execution and is safe to register alongside LangSmith or any other callback.

```python
from qortara_governance import QortaraCallbackHandler
chain.invoke({...}, config={"callbacks": [QortaraCallbackHandler()]})
```

W3C `traceparent` is propagated on every sidecar call, so evidence records and LangSmith traces share trace IDs for correlation.

## Data handling

The SDK forwards the arguments of each intercepted tool call to the sidecar for policy evaluation. Tool arguments may contain sensitive content depending on how your tools are designed. In regulated environments, review which tool arguments will cross the SDK/sidecar boundary and ensure your sidecar deployment — and its storage, if any — satisfies your data-classification requirements.

Subprocess mode keeps all data on `localhost` for the lifetime of the process. Daemon mode depends on the network path and destination you configure.

## Compatibility

| Dependency | Supported |
|---|---|
| Python | 3.10, 3.11, 3.12, 3.13 |
| `langchain-core` | >= 0.3 |
| `langgraph` | >= 0.2 (optional) |

Upcoming LangChain releases are tracked as they land. File an issue if you hit a patching regression on a newer version.

## Status

Alpha. Minor breaking changes may ship before 1.0. No warranty is provided; see [LICENSE](LICENSE). Evaluate carefully before production use and pin to a specific version.

## Security

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md). Do not open public issues for security reports.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributor Covenant applies — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

LangChain, LangGraph, and LangSmith are trademarks of LangChain, Inc. `qortara-governance-langchain` is an independent project and is not affiliated with, endorsed by, or sponsored by LangChain, Inc. Qortara is a trademark of MythologIQ Labs, LLC — see [TRADEMARKS.md](TRADEMARKS.md).
