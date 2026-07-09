"""Permission enforcement (application layer).

Authorization lives here, not in adapters, so every current and future adapter
(Telegram, future web/API) enforces the same rules. Checks are always against
fine-grained permissions (see ``docs/USER_ROLES.md`` §1, §6).
"""

from __future__ import annotations

from donation_bot.application.errors import PermissionDeniedError
from donation_bot.domain.access.entities import StaffUser, permissions_for
from donation_bot.domain.access.permissions import Permission


def require_permission(actor: StaffUser | None, permission: Permission) -> None:
    """Raise :class:`PermissionDeniedError` unless ``actor`` holds ``permission``.

    ``actor is None`` represents an unregistered/public caller, who holds only the
    default public permissions.
    """
    if permission not in permissions_for(actor):
        raise PermissionDeniedError(permission)
