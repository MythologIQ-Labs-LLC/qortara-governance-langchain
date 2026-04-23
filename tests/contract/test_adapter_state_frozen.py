"""AdapterState is a frozen dataclass; mutation attempts raise FrozenInstanceError."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from qortara_governance.contract import AdapterState


def test_adapter_state_is_frozen() -> None:
    state = AdapterState(adapter_name="x", originals={"k": "v"})
    with pytest.raises(FrozenInstanceError):
        state.adapter_name = "y"  # type: ignore[misc]


def test_adapter_state_originals_frozen_field() -> None:
    state = AdapterState(adapter_name="x", originals={"k": "v"})
    with pytest.raises(FrozenInstanceError):
        state.originals = {}  # type: ignore[misc]
