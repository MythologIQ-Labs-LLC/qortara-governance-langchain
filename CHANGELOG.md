# Changelog — qortara-governance-langchain

## v0.1.0 — Unreleased

First public release.

### Added

- `qortara_governance.init()` — one-line integration with LangChain.
- Deep `BaseTool.invoke/ainvoke` + `langgraph.prebuilt.ToolNode.invoke` patches that close the AGT issue #73 wrapper-bypass gap. Native tool-calling dispatch is now governed, not just observed.
- Subprocess auto-spawn + external-daemon opt-in via `QORTARA_SIDECAR_ENDPOINT`.
- HTTP+JSON protocol (v0.1) to the sidecar. Pydantic models shared via `qortara-protocol` package.
- Circuit breaker: consecutive 5xx from the sidecar fails closed to deny-all for a 30s cooldown.
- `QortaraCallbackHandler` — additive observability for chain boundaries and retrieval. Never blocks.
- `@qortara_exempt` decorator for tool opt-out, with evidence still emitted.
- W3C traceparent propagation for LangSmith correlation. `qortara.evidence_id` attaches to the current OTel span.
- `QortaraPolicyDenied`, `QortaraApprovalRequired`, `QortaraSidecarUnavailable` exceptions.
- Unit and integration-with-fakes test suite (24 tests including the AGT #73 bypass-closed regression).

### Not in v0.1

- CrewAI / LlamaIndex / AutoGen adapters — planned as follow-on packages.
- Federation Phase 2 connectors — separate plan.
- Real LangChain version pinning beyond `langchain-core >= 0.3`; upcoming versions tracked as they land.

### License

Apache-2.0.
