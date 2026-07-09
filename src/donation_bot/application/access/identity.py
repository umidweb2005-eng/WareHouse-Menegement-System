"""Identity resolution: map a Telegram ID to a staff actor (or None = public).

A read-only lookup with no permission requirement (resolving *yourself*). Public
users resolve to ``None`` and are never persisted (invariant I1). Adapters call
this to decide which menu to render; use cases still re-check permissions.
"""

from __future__ import annotations

from donation_bot.application.ports.repositories import StaffRepository
from donation_bot.domain.access.entities import StaffUser


def resolve_actor(staff_repo: StaffRepository, telegram_id: int) -> StaffUser | None:
    """Return the active staff user for ``telegram_id``, or None for public users."""
    staff = staff_repo.get_by_telegram_id(telegram_id)
    if staff is None or not staff.is_active or staff.is_system:
        return None
    return staff
