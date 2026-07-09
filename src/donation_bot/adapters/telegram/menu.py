"""Menu section logic (framework-independent).

Given a caller (a staff user or ``None`` for public), decide which main-menu
sections are visible, based purely on permissions (least-privilege UI). This
module has **no** aiogram dependency so it is unit-testable; the keyboard builder
turns these sections into Telegram reply-keyboard buttons.
"""

from __future__ import annotations

from enum import Enum

from donation_bot.domain.access.entities import StaffUser, permissions_for
from donation_bot.domain.access.permissions import Permission


class Section(str, Enum):
    DONATE = "donate"
    REPORTS = "reports"
    STATISTICS = "statistics"
    ABOUT = "about"
    RECORD_DONATION = "record_donation"
    RECORD_EXPENSE = "record_expense"
    MANAGE_STAFF = "manage_staff"
    CONFIGURE_ACCOUNT = "configure_account"
    AUDIT_LOG = "audit_log"


# Ordered by product priority (public first, then treasurer, then admin).
_SECTION_ORDER: tuple[Section, ...] = (
    Section.DONATE,
    Section.REPORTS,
    Section.STATISTICS,
    Section.ABOUT,
    Section.RECORD_DONATION,
    Section.RECORD_EXPENSE,
    Section.MANAGE_STAFF,
    Section.CONFIGURE_ACCOUNT,
    Section.AUDIT_LOG,
)

# Permission gating each section. ``None`` means always visible (public).
_SECTION_PERMISSION: dict[Section, Permission | None] = {
    Section.DONATE: Permission.ACCOUNT_VIEW,
    Section.REPORTS: Permission.REPORT_VIEW,
    Section.STATISTICS: Permission.STATS_VIEW,
    Section.ABOUT: None,
    Section.RECORD_DONATION: Permission.DONATION_RECORD,
    Section.RECORD_EXPENSE: Permission.EXPENSE_RECORD,
    Section.MANAGE_STAFF: Permission.USER_MANAGE,
    Section.CONFIGURE_ACCOUNT: Permission.ACCOUNT_MANAGE,
    Section.AUDIT_LOG: Permission.AUDIT_VIEW,
}

SECTION_LABEL_KEY: dict[Section, str] = {
    Section.DONATE: "menu.donate",
    Section.REPORTS: "menu.reports",
    Section.STATISTICS: "menu.statistics",
    Section.ABOUT: "menu.about",
    Section.RECORD_DONATION: "menu.record_donation",
    Section.RECORD_EXPENSE: "menu.record_expense",
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
