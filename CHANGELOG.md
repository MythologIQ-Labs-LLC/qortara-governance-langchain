# Changelog — qortara-governance-langchain

## v0.2.0 — 2026-04-23

### Added

- `qortara_governance.contract` module — versioned `FrameworkAdapter` Protocol, frozen `AdapterState`, `CONTRACT_VERSION` constant, and an internal `ConformanceSuite` (not re-exported from `__init__` — importable via its module path). This is the extension point for future framework adapters.
- `LangChainToolAdapter` and `LangGraphToolNodeAdapter` — the existing patch logic now implements the `FrameworkAdapter` Protocol. Module-level `apply()` / `unpatch()` functions preserved; the adapter classes delegate to them.
- `AdapterRegistry` replaces the prior module-global patch state. Accepts a sequence of adapters; unwinds LIFO on `unpatch_all()`; rejects version mismatches with `IncompatibleAdapterVersion`.
- `py.typed` marker — signals to mypy/pyright that this package ships type information.

### Changed

- Availability probe in `AdapterRegistry` now uses `importlib.util.find_spec` instead of `importlib.import_module`. Detecting whether a framework is installed no longer triggers that framework's import-time side effects. If `find_spec` resolves but the adapter's own `apply()` raises `ImportError` (broken submodule), the registry skips the adapter with the same `RuntimeWarning` path.
- Module-level `tool_patches.apply()` and `langgraph_patches.apply()` reject double-install — calling `apply()` against `BaseTool.invoke` / `ainvoke` / `ToolNode.invoke` that is already `__qortara_wrapped__` raises `RuntimeError` with a remediation hint.
- `qortara-protocol` dependency pin bumped to `==0.1.2` (additive protocol changes; see qortara-protocol CHANGELOG).

### Fixed

- n/a (no bug fixes; this release is additive + architectural).

### License

Apache-2.0.

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
