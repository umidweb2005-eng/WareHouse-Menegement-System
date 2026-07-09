"""Use case: list recent ledger entries for staff ("So'nggi yozuvlar").

A staff-only, read-only view of individual entries (newest first). It is gated on
the treasurer-level ``entry.annotate`` capability so the public per-entry view
stays closed (public users only ever see aggregate reports). Donations carry no
donor data, so showing amount/date/reference to staff is safe.
"""

from __future__ import annotations

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.ports.read_model import LedgerReadModel
from donation_bot.application.reports.models import EntrySummary
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission


class ListRecentEntries:
    def __init__(self, read_model: LedgerReadModel) -> None:
        self._read_model = read_model

    def execute(self, actor: StaffUser | None, *, limit: int = 15) -> tuple[EntrySummary, ...]:
        require_permission(actor, Permission.ENTRY_ANNOTATE)
        return self._read_model.recent_entries(limit)
