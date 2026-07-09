"""Static in-memory settings provider."""

from __future__ import annotations

from donation_bot.application.ports.settings import LedgerLimits, SettingsProvider


class StaticSettingsProvider(SettingsProvider):
    def __init__(
        self,
        limits: LedgerLimits | None = None,
        org_timezone: str = "Asia/Tashkent",
    ) -> None:
        self._limits = limits or LedgerLimits(
            amount_max_minor=10_000_000_000,  # 100,000,000 so'm
            backdate_window_days=30,
            block_overspend=False,
        )
        self._tz = org_timezone

    def ledger_limits(self) -> LedgerLimits:
        return self._limits

    def org_timezone(self) -> str:
        return self._tz
