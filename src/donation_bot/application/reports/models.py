"""Read-side value objects for reports and statistics.

All figures are derived from the ledger (invariant I5). Public reports include
expense **usage descriptions** but never donor data or private free text.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from donation_bot.domain.money import UZS, Currency, Money


@dataclass(frozen=True, slots=True)
class LedgerTotals:
    """Aggregate totals for a period (or all-time). Net = received - spent."""

    total_in: Money
    total_out: Money
    donation_count: int
    expense_count: int

    @property
    def net(self) -> Money:
        return self.total_in - self.total_out

    @classmethod
    def empty(cls, currency: Currency = UZS) -> "LedgerTotals":
        return cls(Money.zero(currency), Money.zero(currency), 0, 0)


@dataclass(frozen=True, slots=True)
class ExpenseLine:
    """A single public expense usage line (how donations were used)."""

    reference_no: int
    amount: Money
    category_id: int
    description: str
    event_at: datetime


@dataclass(frozen=True, slots=True)
class PeriodReport:
    label: str
    totals: LedgerTotals
    expense_lines: tuple[ExpenseLine, ...]


@dataclass(frozen=True, slots=True)
class Statistics:
    """Daily / monthly / yearly / all-time snapshot, generated at a point in time."""

    generated_at: datetime
    today: LedgerTotals
    this_month: LedgerTotals
    this_year: LedgerTotals
    all_time: LedgerTotals
