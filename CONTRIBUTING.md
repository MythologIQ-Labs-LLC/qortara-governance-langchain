# Contributing

Thanks for your interest in contributing. This document covers local setup, how to propose a change, and what reviewers look for.

## Ground rules

- Be civil. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Security-sensitive issues go through private disclosure — see [SECURITY.md](SECURITY.md), not the public tracker.
- Non-trivial changes benefit from an issue discussion before a PR. If you're unsure whether a change is non-trivial, open the issue first.

## Local setup

This package uses [`uv`](https://docs.astral.sh/uv/) for environment management.

```bash
git clone https://github.com/MythologIQ-Labs-LLC/qortara-governance-langchain.git
cd qortara-governance-langchain
uv sync --all-extras
uv run pytest
```

`pytest` must pass before opening a PR. The suite includes regression tests for the `BaseTool` and `ToolNode` patch surfaces; those are load-bearing and should stay green.

## Style

- Format with `ruff format`.
- Lint with `ruff check`.
- Type-check with `mypy src` — the public API should remain fully typed.
- Keep docstrings terse and action-oriented. Avoid marketing prose.

Both `ruff` and `mypy` are run in CI on every PR.

## Scope of this package

This repository ships the client-side SDK only: patches, config resolution, the sidecar HTTP client, and the public exception surface. The sidecar itself and the policy decision engine are not part of this repository.

Changes welcomed in-scope:

- LangChain / LangGraph version compatibility
- New framework adapters (see below)
- Patch hardening, better test coverage, ergonomic improvements to the public API
- Documentation, examples, error-message clarity

Out of scope here (handle elsewhere):

- Policy language changes
- Sidecar wire-protocol changes — submit as an issue first, we'll coordinate
- Hosted decision-plane behavior

## Adapter extensions

CrewAI, LlamaIndex, AutoGen, and similar framework adapters are welcome as follow-on packages (`qortara-governance-<framework>`) that depend on this one. Open an issue to discuss the shape before writing a full implementation — we're keeping the core patch surface small on purpose.

## Pull request process

1. Fork and branch from `main`.
2. Keep the diff focused. Prefer multiple small PRs over one large one.
3. Add or update tests. Patches without tests will usually bounce.
4. Update `CHANGELOG.md` under the unreleased section.
5. Run `uv run pytest`, `ruff check`, `ruff format --check`, and `mypy src` locally before pushing.
6. Open the PR against `main`. Fill in the PR template. CI must be green for review.
7. Reviewers may ask for changes; please treat review comments as conversational, not adversarial.

## DCO

Commits must be signed off under the [Developer Certificate of Origin](https://developercertificate.org/):

```bash
git commit -s -m "your message"
```

The `-s` flag appends a `Signed-off-by` line. This is an assertion that you have the right to contribute the change under the repository's Apache-2.0 license.

## Reporting bugs

File an issue using the bug-report template. Useful reports include:

- Python version and OS
- `langchain-core` version, and `langgraph` version if applicable
- Minimal reproduction — ideally < 30 lines
- Expected vs. actual behavior
- Full stack trace if the SDK raised

## Proposing features

File an issue using the feature-request template. Good proposals describe the use case first and the mechanism second. We're biased toward small, composable additions.
