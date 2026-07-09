"""Shared validation for recording ledger entries (BR-M4 amount ceiling, BR-L7 dates).

The warn-threshold that prompts an extra UI confirmation is intentionally *not*
enforced here — that is a presentation concern. The application layer enforces the
hard maximum and the event-time bounds.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from donation_bot.application.errors import (
    AmountLimitExceededError,
    InvalidEventTimeError,
)
from donation_bot.application.ports.settings import LedgerLimits
from donation_bot.domain.money import Money


def validate_amount(amount: Money, limits: LedgerLimits) -> None:
    # Positivity is enforced by the domain entity; here we enforce the hard cap.
    if amount.amount_minor > limits.amount_max_minor:
        raise AmountLimitExceededError(
            f"amount {amount.amount_minor} exceeds maximum {limits.amount_max_minor}"
        )


def validate_event_time(event_at: datetime, now: datetime, limits: LedgerLimits) -> None:
    if event_at > now:
        raise InvalidEventTimeError("event time must not be in the future")
    earliest = now - timedelta(days=limits.backdate_window_days)
    if event_at < earliest:
        raise InvalidEventTimeError(
            f"event time is older than the allowed back-date window "
            f"({limits.backdate_window_days} days)"
        )
