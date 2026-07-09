"""Application-layer error types.

Distinct from domain errors: these represent use-case level failures (missing
permission, not found, policy violation). Adapters map them to localized user
messages; they never leak internals.
"""

from __future__ import annotations

from donation_bot.domain.access.permissions import Permission


class ApplicationError(Exception):
    """Base class for application/use-case errors."""


class PermissionDeniedError(ApplicationError):
    def __init__(self, permission: Permission) -> None:
        self.permission = permission
        super().__init__(f"missing permission: {permission.value}")


class EntryNotFoundError(ApplicationError):
    """Raised when a referenced ledger entry does not exist."""


class AnnotationNotFoundError(ApplicationError):
    """Raised when a referenced annotation does not exist."""


class AlreadyReversedError(ApplicationError):
    """Raised when reversing an entry that already has a reversal (BR-L3)."""


class AmountLimitExceededError(ApplicationError):
    """Raised when an amount exceeds the configured hard maximum (BR-M4)."""


class InvalidEventTimeError(ApplicationError):
    """Raised when event_at is in the future or older than the backdate window (BR-L7)."""


class OverspendError(ApplicationError):
    """Raised when an expense would drive the balance negative and blocking is on (BR-E4)."""
