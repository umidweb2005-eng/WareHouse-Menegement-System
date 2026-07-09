"""Reporting & statistics service (BR-R / BR-S).

Every figure is derived from the ledger via the read-model port; nothing is
hand-entered. Period bucketing uses the organization time zone; storage is UTC.
Public reports expose expense usage descriptions but never donor data or private
free text. Report/statistics reads are public (``report.view`` / ``stats.view``),
so a ``None`` actor (unregistered) is allowed by default.
"""

from __future__ import annotations

from datetime import date

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.read_model import LedgerReadModel
from donation_bot.application.ports.settings import SettingsProvider
from donation_bot.application.reports.models import PeriodReport, Statistics
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.time import Period, day_period, month_period, year_period


class ReportService:
    def __init__(
        self,
        read_model: LedgerReadModel,
        clock: Clock,
        settings: SettingsProvider,
    ) -> None:
        self._read_model = read_model
        self._clock = clock
        self._settings = settings

    # -- reports -------------------------------------------------------------
    def report_for(self, period: Period | None, *, actor: StaffUser | None = None) -> PeriodReport:
        require_permission(actor, Permission.REPORT_VIEW)
        totals = self._read_model.totals(period)
        lines = self._read_model.expense_lines(period)
        label = period.label if period is not None else "all-time"
        return PeriodReport(label=label, totals=totals, expense_lines=lines)

    def daily_report(self, day: date, *, actor: StaffUser | None = None) -> PeriodReport:
        return self.report_for(day_period(day, self._tz()), actor=actor)

    def monthly_report(
        self, year: int, month: int, *, actor: StaffUser | None = None
    ) -> PeriodReport:
        return self.report_for(month_period(year, month, self._tz()), actor=actor)

    def yearly_report(self, year: int, *, actor: StaffUser | None = None) -> PeriodReport:
        return self.report_for(year_period(year, self._tz()), actor=actor)

    def total_report(self, *, actor: StaffUser | None = None) -> PeriodReport:
        return self.report_for(None, actor=actor)

    # -- statistics ----------------------------------------------------------
    def statistics(self, *, actor: StaffUser | None = None) -> Statistics:
        require_permission(actor, Permission.STATS_VIEW)
        tz = self._tz()
        now = self._clock.now()
        local_today = now.astimezone(_zone(tz)).date()
        return Statistics(
            generated_at=now,
            today=self._read_model.totals(day_period(local_today, tz)),
            this_month=self._read_model.totals(
                month_period(local_today.year, local_today.month, tz)
            ),
            this_year=self._read_model.totals(year_period(local_today.year, tz)),
            all_time=self._read_model.totals(None),
        )

    # -- helpers -------------------------------------------------------------
    def _tz(self) -> str:
        return self._settings.org_timezone()


def _zone(tz: str):  # small local import to keep zoneinfo usage contained
    from zoneinfo import ZoneInfo

    return ZoneInfo(tz)
