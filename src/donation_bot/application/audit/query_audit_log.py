"""Use case: view the audit log (BR-AU4, ``audit.view`` / Super Admin).

A read-only query over the append-only audit log. Audit entries never contain
donor identity or private free text, so returning them is safe.
"""

from __future__ import annotations

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import AuditEntry
from donation_bot.application.ports.repositories import AuditLogRepository
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission


class QueryAuditLog:
    def __init__(self, audit_repo: AuditLogRepository) -> None:
        self._audit = audit_repo

    def execute(self, actor: StaffUser | None, *, limit: int = 20) -> tuple[AuditEntry, ...]:
        require_permission(actor, Permission.AUDIT_VIEW)
        return self._audit.list_recent(limit)
