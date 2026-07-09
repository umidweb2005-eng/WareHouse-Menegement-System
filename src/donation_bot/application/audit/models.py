"""Audit entry model and action constants.

Audit entries are append-only and must never contain donor identity or private
free text (annotation / reversal-reason content) — see BR-AU3/BR-X4. Summaries
carry only structured, non-PII facts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime


# Action codes (stable strings used in the audit log).
DONATION_RECORDED = "donation.recorded"
EXPENSE_RECORDED = "expense.recorded"
ENTRY_REVERSED = "entry.reversed"
ANNOTATION_ADDED = "annotation.added"
ANNOTATION_REDACTED = "annotation.redacted"
STAFF_REGISTERED = "staff.registered"
STAFF_SEEDED = "staff.seeded"
ACCOUNT_CONFIGURED = "account.configured"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    entity_type: str
    actor_user_id: str | None
    created_at: datetime
    entity_id: str | None = None
    entity_ref: int | None = None
    summary: Mapping[str, object] = field(default_factory=dict)
    audit_id: str | None = None
