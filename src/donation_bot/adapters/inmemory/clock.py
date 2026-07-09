"""In-memory clocks."""

from __future__ import annotations

from datetime import datetime, timezone

from donation_bot.application.ports.clock import Clock


class ManualClock(Clock):
    """A clock whose time is set explicitly (deterministic tests)."""

    def __init__(self, now: datetime) -> None:
        if now.tzinfo is None:
            raise ValueError("ManualClock requires a timezone-aware datetime")
        self._now = now.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now.astimezone(timezone.utc)
