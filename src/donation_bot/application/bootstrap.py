"""First-run seeding.

Idempotently ensures the reserved **system actor** and the **first Super Admin**
(from configuration) exist. Safe to call on every startup. See
``docs/USER_ROLES.md`` §5 and ``docs/DATABASE_DESIGN.md`` §12.
"""

from __future__ import annotations

from collections.abc import Callable

from donation_bot.application.audit.models import STAFF_SEEDED, AuditEntry
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import (
    SUPER_ADMIN_ROLE,
    SYSTEM_ACTOR_USER_ID,
    StaffUser,
    system_actor,
)


def ensure_seed(
    uow_factory: Callable[[], UnitOfWork],
    clock: Clock,
    id_generator: IdGenerator,
    *,
    first_super_admin_telegram_id: int,
    first_super_admin_name: str | None = None,
) -> None:
    now = clock.now()
    with uow_factory() as uow:
        # Reserved system actor (authors machine-initiated records).
        if uow.staff.get(SYSTEM_ACTOR_USER_ID) is None:
            uow.staff.add(system_actor())

        # First Super Admin (break-glass friendly: re-seeds if absent).
        if uow.staff.get_by_telegram_id(first_super_admin_telegram_id) is None:
            admin = StaffUser(
                user_id=id_generator.new_id(),
                telegram_id=first_super_admin_telegram_id,
                roles=frozenset({SUPER_ADMIN_ROLE}),
                display_name=first_super_admin_name,
            )
            uow.staff.add(admin)
            uow.audit.add(
                AuditEntry(
                    action=STAFF_SEEDED,
                    entity_type="staff_user",
                    actor_user_id=None,  # system/bootstrap action
                    created_at=now,
                    entity_id=admin.user_id,
                    summary={"role": SUPER_ADMIN_ROLE.code, "telegram_id": first_super_admin_telegram_id},
                )
            )
