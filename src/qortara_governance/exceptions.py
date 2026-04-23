"""Public exceptions raised by Qortara Governance SDK."""

from __future__ import annotations


class QortaraError(Exception):
    """Base for all SDK-raised errors."""


class QortaraPolicyDenied(QortaraError):
    """Sidecar returned decision_kind=deny for the attempted action."""

    def __init__(
        self, rationale: str, policy_pack_id: str, policy_version_sha256: str
    ) -> None:
        self.rationale = rationale
        self.policy_pack_id = policy_pack_id
        self.policy_version_sha256 = policy_version_sha256
        super().__init__(f"[{policy_pack_id}] {rationale}")


class QortaraApprovalRequired(QortaraError):
    """Sidecar returned decision_kind=require_approval; caller must obtain approval."""

    def __init__(
        self, rationale: str, approval_url: str | None, policy_pack_id: str
    ) -> None:
        self.rationale = rationale
        self.approval_url = approval_url
        self.policy_pack_id = policy_pack_id
        super().__init__(f"[{policy_pack_id}] approval required: {rationale}")


class QortaraSidecarUnavailable(QortaraError):
    """Sidecar unreachable and circuit breaker has tripped."""
