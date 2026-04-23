"""LangChainToolAdapter satisfies the FrameworkAdapter ConformanceSuite."""

from __future__ import annotations

from qortara_governance.contract import FrameworkAdapter
from qortara_governance.contract.conformance import ConformanceSuite
from qortara_governance.patches.tool_patches import LangChainToolAdapter


def test_langchain_tool_adapter_is_framework_adapter() -> None:
    assert isinstance(LangChainToolAdapter(), FrameworkAdapter)


def test_langchain_tool_adapter_contract_version(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangChainToolAdapter(), fake_client_factory
    ).test_contract_version_matches()


def test_langchain_tool_adapter_state_roundtrip(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(LangChainToolAdapter(), fake_client_factory).test_state_roundtrip()


def test_langchain_tool_adapter_unpatch_byte_identical(
    fake_client_factory,  # noqa: ANN001
) -> None:
    ConformanceSuite(
        LangChainToolAdapter(), fake_client_factory
    ).test_unpatch_restores_byte_identical()


def test_langchain_tool_adapter_apply_idempotent(fake_client_factory) -> None:  # noqa: ANN001
    ConformanceSuite(
        LangChainToolAdapter(), fake_client_factory
    ).test_apply_is_idempotent()
