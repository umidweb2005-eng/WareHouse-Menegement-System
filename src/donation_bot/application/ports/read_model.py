"""Read-model port: derived, aggregate reads for reports and statistics.

Speaks in aggregates (sums/counts) and usage lines so a SQL adapter can express
them as ``SUM``/``COUNT``/``GROUP BY``. ``period=None`` means all-time. Reversed
entries and their reversals net to zero in the totals (invariant I3/I5).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from donation_bot.application.reports.models import EntrySummary, ExpenseLine, LedgerTotals
from donation_bot.domain.time import Period


class LedgerReadModel(ABC):
    @abstractmethod
    def totals(self, period: Period | None) -> LedgerTotals:
        """Aggregate totals over ``period`` (or all-time when ``None``)."""

    @abstractmethod
    def expense_lines(self, period: Period | None) -> tuple[ExpenseLine, ...]:
        """Public expense usage lines over ``period`` (active, i.e., not reversed)."""

    @abstractmethod
    def recent_entries(self, limit: int = 15) -> tuple[EntrySummary, ...]:
        """Most recent original entries (newest first), with a reversed flag.

        Staff-only view (individual entries); never exposed to public users.
        """
