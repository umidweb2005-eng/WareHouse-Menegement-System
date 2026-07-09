"""The v1 permission catalog.

Authorization is always checked against these fine-grained permissions, never
against role names (see ``docs/USER_ROLES.md`` §1). New permissions are added here
as features ship (e.g., receipt permissions in Version 2).
"""

from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    # Public (granted by default to everyone, including unregistered chats)
    REPORT_VIEW = "report.view"
    STATS_VIEW = "stats.view"
    ACCOUNT_VIEW = "account.view"

    # Treasurer
    DONATION_RECORD = "donation.record"
    DONATION_REVERSE = "donation.reverse"
    EXPENSE_RECORD = "expense.record"
    EXPENSE_REVERSE = "expense.reverse"
    ENTRY_ANNOTATE = "entry.annotate"

    # Super Admin (governance)
    USER_MANAGE = "user.manage"
    ROLE_MANAGE = "role.manage"
    CATEGORY_MANAGE = "category.manage"
    SETTINGS_MANAGE = "settings.manage"
    ACCOUNT_MANAGE = "account.manage"
    AUDIT_VIEW = "audit.view"
    PII_ERASE = "pii.erase"
    BACKUP_MANAGE = "backup.manage"


# Permissions available to any bot user without registration (transparency).
PUBLIC_PERMISSIONS: frozenset[Permission] = frozenset(
    {Permission.REPORT_VIEW, Permission.STATS_VIEW, Permission.ACCOUNT_VIEW}
)

TREASURER_PERMISSIONS: frozenset[Permission] = PUBLIC_PERMISSIONS | frozenset(
    {
        Permission.DONATION_RECORD,
        Permission.DONATION_REVERSE,
        Permission.EXPENSE_RECORD,
        Permission.EXPENSE_REVERSE,
        Permission.ENTRY_ANNOTATE,
    }
)

# Super Admin holds every permission in the catalog.
SUPER_ADMIN_PERMISSIONS: frozenset[Permission] = frozenset(Permission)
