"""Menu section logic (framework-independent).

Given a caller (a staff user or ``None`` for public), decide which main-menu
sections are visible, based purely on permissions (least-privilege UI). No aiogram
dependency, so it is unit-testable; the keyboard builder turns these sections into
Telegram reply-keyboard buttons (rendered two per row).
"""

from __future__ import annotations

from enum import Enum

from donation_bot.domain.access.entities import StaffUser, permissions_for
from donation_bot.domain.access.permissions import Permission


class Section(str, Enum):
    DONATE = "donate"
    STATISTICS = "statistics"
    REPORTS = "reports"
    RECORD_DONATION = "record_donation"
    RECORD_EXPENSE = "record_expense"
    RECENT_ENTRIES = "recent_entries"
    MANAGE_STAFF = "manage_staff"
    CONFIGURE_ACCOUNT = "configure_account"
    AUDIT_LOG = "audit_log"


# Display order (rendered two buttons per row): public → treasurer → admin.
_SECTION_ORDER: tuple[Section, ...] = (
    Section.DONATE,
    Section.STATISTICS,
    Section.REPORTS,
    Section.RECORD_DONATION,
    Section.RECORD_EXPENSE,
    Section.RECENT_ENTRIES,
    Section.MANAGE_STAFF,
    Section.CONFIGURE_ACCOUNT,
    Section.AUDIT_LOG,
)

# Permission gating each section. ``None`` means always visible (public).
_SECTION_PERMISSION: dict[Section, Permission | None] = {
    Section.DONATE: Permission.ACCOUNT_VIEW,
    Section.STATISTICS: Permission.STATS_VIEW,
    Section.REPORTS: Permission.REPORT_VIEW,
    Section.RECORD_DONATION: Permission.DONATION_RECORD,
    Section.RECORD_EXPENSE: Permission.EXPENSE_RECORD,
    # Recent entries lists individual (staff-only) ledger entries; gated on the
    # treasurer-level annotate capability so the public per-entry view stays closed.
    Section.RECENT_ENTRIES: Permission.ENTRY_ANNOTATE,
    Section.MANAGE_STAFF: Permission.USER_MANAGE,
    Section.CONFIGURE_ACCOUNT: Permission.ACCOUNT_MANAGE,
    Section.AUDIT_LOG: Permission.AUDIT_VIEW,
}

SECTION_LABEL_KEY: dict[Section, str] = {
    Section.DONATE: "menu.donate",
    Section.STATISTICS: "menu.statistics",
    Section.REPORTS: "menu.reports",
    Section.RECORD_DONATION: "menu.record_donation",
    Section.RECORD_EXPENSE: "menu.record_expense",
    Section.RECENT_ENTRIES: "menu.recent_entries",
    Section.MANAGE_STAFF: "menu.manage_staff",
    Section.CONFIGURE_ACCOUNT: "menu.configure_account",
    Section.AUDIT_LOG: "menu.audit_log",
}


def main_sections(actor: StaffUser | None) -> list[Section]:
    """Return the visible menu sections for ``actor`` in display order."""
    granted = permissions_for(actor)
    result: list[Section] = []
    for section in _SECTION_ORDER:
        permission = _SECTION_PERMISSION[section]
        if permission is None or permission in granted:
            result.append(section)
    return result
