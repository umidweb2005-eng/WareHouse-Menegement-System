"""System clock adapter (real wall-clock UTC)."""

from __future__ import annotations

from datetime import datetime, timezone

from donation_bot.application.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
