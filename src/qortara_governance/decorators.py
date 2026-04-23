"""@qortara_exempt — opt-out marker for tools that must bypass enforcement."""

from __future__ import annotations

from typing import TypeVar

_EXEMPT_ATTR = "__qortara_exempt__"

T = TypeVar("T")


def qortara_exempt(obj: T) -> T:
    """Mark a tool class or instance as exempt from Qortara policy enforcement.

    Exempt tools still emit evidence (decision_kind=exempt) for audit completeness,
    but never trigger policy evaluation or deny responses.
    """
    setattr(obj, _EXEMPT_ATTR, True)
    return obj


def is_exempt(obj: object) -> bool:
    """Return True if the object or its class is marked exempt."""
    if getattr(obj, _EXEMPT_ATTR, False):
        return True
    cls = type(obj)
    return bool(getattr(cls, _EXEMPT_ATTR, False))
