"""Button label constants for reply-keyboard routing.

Reply keyboards send the button's *text*, so handlers route by matching that text.
The labels are sourced from the default-locale (Uzbek) catalog, so they always
match what the keyboard builder renders. (Routing by text is single-locale in v1;
adding locales later would extend this mapping.)
"""

from __future__ import annotations

from donation_bot.adapters.telegram.support import EXPENSE_CATEGORIES
from donation_bot.infrastructure.i18n.translator import CATALOG, DEFAULT_LOCALE

_UZ = CATALOG[DEFAULT_LOCALE]


def _l(key: str) -> str:
    return _UZ.get(key, f"<{key}>")


# Main menu
DONATE = _l("menu.donate")
STATISTICS = _l("menu.statistics")
REPORTS = _l("menu.reports")
RECORD_DONATION = _l("menu.record_donation")
RECORD_EXPENSE = _l("menu.record_expense")
RECENT_ENTRIES = _l("menu.recent_entries")
MANAGE_STAFF = _l("menu.manage_staff")
CONFIGURE_ACCOUNT = _l("menu.configure_account")
AUDIT_LOG = _l("menu.audit_log")

# Navigation / common
BACK = _l("common.back")
CANCEL = _l("common.cancel")
CONFIRM = _l("common.confirm")
SKIP = _l("common.skip")

# Report periods
REP_TODAY = _l("reports.today")
REP_MONTH = _l("reports.month")
REP_YEAR = _l("reports.year")
REP_ALL = _l("reports.all_time")

# Donation sources
SRC_CASH = _l("donation.source_cash")
SRC_BANK = _l("donation.source_bank")

# Staff roles
ROLE_TREASURER = _l("staff.role_treasurer")
ROLE_ADMIN = _l("staff.role_admin")

# Account types
ACC_CARD = _l("account.type_card")
ACC_BANK = _l("account.type_bank")
ACC_WALLET = _l("account.type_wallet")

# Expense categories: label text -> category id (for routing category selection)
CATEGORY_ID_BY_LABEL: dict[str, int] = {name: cid for cid, name in EXPENSE_CATEGORIES.items()}
