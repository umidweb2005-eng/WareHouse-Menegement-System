"""Domain-level error types.

The domain raises typed errors; adapters (e.g., the Telegram layer) map them to
friendly, localized messages. Domain code never raises framework-specific errors.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class CurrencyMismatchError(DomainError):
    """Raised when money in different currencies is combined."""


class InvalidMoneyError(DomainError):
    """Raised for malformed monetary values (e.g., non-integer minor units)."""


class InvalidLedgerEntryError(DomainError):
    """Raised when a ledger entry violates its construction invariants."""


class ReversalError(DomainError):
    """Raised for invalid reversal operations (e.g., reversing a reversal)."""
