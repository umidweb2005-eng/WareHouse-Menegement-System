"""Use case: register a new staff member by Telegram ID (BR: chain of trust).

Only a holder of ``user.manage`` (Super Admin) may register staff. No self-signup.
Storing a staff Telegram ID is operator identity for authorization/audit, not
donor data.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import STAFF_REGISTERED, AuditEntry
from donation_bot.application.errors import StaffAlreadyRegisteredError
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import Role, StaffUser
from donation_bot.domain.access.permissions import Permission


@dataclass(frozen=True, slots=True)
class RegisterStaffCommand:
    actor: StaffUser
    telegram_id: int
    role: Role
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterStaffResult:
    user_id: str


class RegisterStaff:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator

    def execute(self, command: RegisterStaffCommand) -> RegisterStaffResult:
        require_permission(command.actor, Permission.USER_MANAGE)
        now = self._clock.now()
        with self._uow_factory() as uow:
            if uow.staff.get_by_telegram_id(command.telegram_id) is not None:
                raise StaffAlreadyRegisteredError(
                    f"telegram id {command.telegram_id} is already registered"
                )
            staff = StaffUser(
                user_id=self._ids.new_id(),
                telegram_id=command.telegram_id,
                roles=frozenset({command.role}),
                display_name=command.display_name,
            )
            stored = uow.staff.add(staff)
            uow.audit.add(
                AuditEntry(
                    action=STAFF_REGISTERED,
                    entity_type="staff_user",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.user_id,
                    summary={"role": command.role.code, "telegram_id": command.telegram_id},
                )
            )
        return RegisterStaffResult(user_id=stored.user_id)
