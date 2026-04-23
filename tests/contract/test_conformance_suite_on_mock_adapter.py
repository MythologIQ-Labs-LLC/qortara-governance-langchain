"""A deliberately-wrong mock adapter fails each ConformanceSuite invariant."""

from __future__ import annotations

import pytest

from qortara_governance.contract import AdapterState
from qortara_governance.contract.conformance import ConformanceSuite
from qortara_governance.contract.state import CONTRACT_VERSION


class _WrongVersionAdapter:
    name = "wrong-version"
    framework_module = "builtins"
    contract_version = "9.9"

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name=self.name, originals={"noop": object()})

    def unpatch(self, state):  # noqa: ANN001, ANN201
        return None


class _WrongNameAdapter:
    name = "declared"
    framework_module = "builtins"
    contract_version = CONTRACT_VERSION

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name="different", originals={"noop": object()})

    def unpatch(self, state):  # noqa: ANN001, ANN201
        return None


class _NotRestoringAdapter:
    """apply returns differing object identities each call → byte-identity fails."""

    name = "not-restoring"
    framework_module = "builtins"
    contract_version = CONTRACT_VERSION

    def apply(self, client):  # noqa: ANN001, ANN201
        return AdapterState(adapter_name=self.name, originals={"m": object()})

    def unpatch(self, state):  # noqa: ANN001, ANN201
        return None


def test_version_mismatch_fails_version_invariant(fake_client_factory) -> None:  # noqa: ANN001
    suite = ConformanceSuite(_WrongVersionAdapter(), fake_client_factory)
    with pytest.raises(AssertionError, match="contract_version"):
        suite.test_contract_version_matches()


def test_wrong_name_fails_state_roundtrip(fake_client_factory) -> None:  # noqa: ANN001
    suite = ConformanceSuite(_WrongNameAdapter(), fake_client_factory)
    with pytest.raises(AssertionError, match="adapter_name"):
        suite.test_state_roundtrip()


def test_fresh_identities_fail_byte_identical_invariant(fake_client_factory) -> None:  # noqa: ANN001
    suite = ConformanceSuite(_NotRestoringAdapter(), fake_client_factory)
    with pytest.raises(AssertionError, match="byte-identical"):
        suite.test_unpatch_restores_byte_identical()
