"""Use cases for the public donation account (BR-AC).

``ConfigureDonationAccount`` appends a new account row (becomes active); reading
the active account is public. See ``docs/BUSINESS_RULES.md`` §8.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import ACCOUNT_CONFIGURED, AuditEntry
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.repositories import DonationAccountRepository
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.accounts.entities import AccountType, DonationAccount
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission


@dataclass(frozen=True, slots=True)
class ConfigureDonationAccountCommand:
    actor: StaffUser
    label: str
    account_type: AccountType
    account_value: str | None
    holder_name: str | None = None


@dataclass(frozen=True, slots=True)
class ConfigureDonationAccountResult:
    account_id: str


class ConfigureDonationAccount:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator

    def execute(self, command: ConfigureDonationAccountCommand) -> ConfigureDonationAccountResult:
        require_permission(command.actor, Permission.ACCOUNT_MANAGE)
        now = self._clock.now()
        account = DonationAccount(
            label=command.label,
            account_type=command.account_type,
            account_value=command.account_value,
            holder_name=command.holder_name,
            created_by=command.actor.user_id,
            created_at=now,
            account_id=self._ids.new_id(),
        )
        with self._uow_factory() as uow:
            stored = uow.accounts.add(account)
            uow.audit.add(
                AuditEntry(
                    action=ACCOUNT_CONFIGURED,
                    entity_type="donation_account",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.account_id,
                    summary={"label": command.label, "type": command.account_type.value},
                )
            )
        assert stored.account_id is not None
        return ConfigureDonationAccountResult(account_id=stored.account_id)


class GetActiveDonationAccount:
    """Read the current public donation account (``account.view``, public)."""

    def __init__(self, account_repo: DonationAccountRepository) -> None:
        self._accounts = account_repo

    def execute(self, actor: StaffUser | None = None) -> DonationAccount | None:
        require_permission(actor, Permission.ACCOUNT_VIEW)
        return self._accounts.active()
