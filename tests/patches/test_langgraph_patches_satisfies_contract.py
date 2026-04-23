"""LangGraphToolNodeAdapter satisfies the FrameworkAdapter ConformanceSuite.

Skipped when langgraph is not installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("langgraph")

from qortara_governance.contract import FrameworkAdapter  # noqa: E402
from qortara_governance.contract.conformance import ConformanceSuite  # noqa: E402
from qortara_governance.patches.langgraph_patches import (  # noqa: E402
    LangGraphToolNodeAdapter,
)


def test_langgraph_adapter_is_framework_adapter() -> None:
    assert isinstance(LangGraphToolNodeAdapter(), FrameworkAdapter)


def test_langgraph_adapter_contract_version(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangGraphToolNodeAdapter(), fake_client_factory
    ).test_contract_version_matches()


def test_langgraph_adapter_state_roundtrip(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangGraphToolNodeAdapter(), fake_client_factory
    ).test_state_roundtrip()


def test_langgraph_adapter_unpatch_byte_identical(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangGraphToolNodeAdapter(), fake_client_factory
    ).test_unpatch_restores_byte_identical()


def test_langgraph_adapter_apply_idempotent(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangGraphToolNodeAdapter(), fake_client_factory
    ).test_apply_is_idempotent()
