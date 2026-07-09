"""In-memory read model over :class:`InMemoryStore`.

Computes the same aggregates a SQL adapter would (SUM/COUNT/GROUP BY). Reversed
originals are excluded entirely, so a reversed pair contributes zero to totals and
never appears in the public expense usage lines (invariant I3/I5).
"""

from __future__ import annotations

from donation_bot.adapters.inmemory.store import InMemoryStore
from donation_bot.application.ports.read_model import LedgerReadModel
from donation_bot.application.reports.models import EntrySummary, ExpenseLine, LedgerTotals
from donation_bot.domain.ledger.entities import EntryKind, LedgerEntry
from donation_bot.domain.money import UZS, Money
from donation_bot.domain.time import Period


class InMemoryLedgerReadModel(LedgerReadModel):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def _active_originals_in(self, period: Period | None) -> list[LedgerEntry]:
        result: list[LedgerEntry] = []
        for entry in self._store.entries.values():
            if entry.entry_id in self._store.reversed_original_ids:
                continue  # reversed -> excluded
            if period is not None and not period.contains(entry.event_at):
                continue
            result.append(entry)
        return result

    def totals(self, period: Period | None) -> LedgerTotals:
        total_in = Money.zero(UZS)
        total_out = Money.zero(UZS)
        donation_count = 0
        expense_count = 0
        for entry in self._active_originals_in(period):
            if entry.kind is EntryKind.DONATION:
                total_in = total_in + entry.amount
                donation_count += 1
            else:
                total_out = total_out + entry.amount
                expense_count += 1
        return LedgerTotals(total_in, total_out, donation_count, expense_count)

    def expense_lines(self, period: Period | None) -> tuple[ExpenseLine, ...]:
        lines: list[ExpenseLine] = []
        for entry in self._active_originals_in(period):
            if entry.kind is not EntryKind.EXPENSE:
                continue
            assert entry.reference_no is not None
            assert entry.expense_category_id is not None
            assert entry.expense_description is not None
            lines.append(
                ExpenseLine(
                    reference_no=entry.reference_no,
                    amount=entry.amount,
                    category_id=entry.expense_category_id,
                    description=entry.expense_description,
                    event_at=entry.event_at,
                )
            )
        lines.sort(key=lambda line: line.reference_no)
        return tuple(lines)

    def recent_entries(self, limit: int = 15) -> tuple[EntrySummary, ...]:
        originals = sorted(
            self._store.entries.values(),
            key=lambda e: e.reference_no or 0,
            reverse=True,  # newest first
        )
        summaries: list[EntrySummary] = []
        for entry in originals[:limit]:
            assert entry.reference_no is not None
            summaries.append(
                EntrySummary(
                    reference_no=entry.reference_no,
                    kind=entry.kind.value,
                    amount=entry.amount,
                    event_at=entry.event_at,
                    is_reversed=entry.entry_id in self._store.reversed_original_ids,
                    description=entry.expense_description,
                )
            )
        return tuple(summaries)
