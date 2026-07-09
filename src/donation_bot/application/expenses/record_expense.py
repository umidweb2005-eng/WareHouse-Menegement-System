"""Use case: record an expense / usage of funds (BR-E).

Records how donations were used. The amount and a required **public** usage
description go on the immutable entry; an optional private note goes to an
annotation. Overspend handling is best-effort per BR-E4 (warn by default; hard
block only when the policy is enabled).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import EXPENSE_RECORDED, AuditEntry
from donation_bot.application.errors import OverspendError
from donation_bot.application.ledger.validation import validate_amount, validate_event_time
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.read_model import LedgerReadModel
from donation_bot.application.ports.settings import SettingsProvider
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.annotations.entities import Annotation, AnnotationType
from donation_bot.domain.ledger.entities import record_expense
from donation_bot.domain.money import Money


@dataclass(frozen=True, slots=True)
class RecordExpenseCommand:
    actor: StaffUser
    amount: Money
    category_id: int
    description: str  # PUBLIC usage description (required)
    event_at: datetime
    note: str | None = None  # optional PRIVATE annotation


@dataclass(frozen=True, slots=True)
class RecordExpenseResult:
    entry_id: str
    reference_no: int
    overspent: bool  # True if this expense drives the running balance negative


class RecordExpense:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
        settings: SettingsProvider,
        read_model: LedgerReadModel,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator
        self._settings = settings
        self._read_model = read_model

    def execute(self, command: RecordExpenseCommand) -> RecordExpenseResult:
        require_permission(command.actor, Permission.EXPENSE_RECORD)

        limits = self._settings.ledger_limits()
        now = self._clock.now()
        validate_amount(command.amount, limits)
        validate_event_time(command.event_at, now, limits)

        # Best-effort overspend check (BR-E4). Derived from the ledger.
        current_net = self._read_model.totals(None).net
        overspent = (current_net - command.amount).is_negative
        if overspent and limits.block_overspend:
            raise OverspendError("expense would drive the balance negative")

        entry = record_expense(
            amount=command.amount,
            category_id=command.category_id,
            description=command.description,
            event_at=command.event_at,
            recorded_by=command.actor.user_id,
            entry_id=self._ids.new_id(),
            recorded_at=now,
        )

        with self._uow_factory() as uow:
            stored = uow.ledger.add_entry(entry)
            if command.note and command.note.strip():
                uow.annotations.add(
                    Annotation(
                        entry_id=stored.entry_id,
                        annotation_type=AnnotationType.NOTE,
                        author_id=command.actor.user_id,
                        content=command.note,
                        created_at=now,
                        annotation_id=self._ids.new_id(),
                    )
                )
            uow.audit.add(
                AuditEntry(
                    action=EXPENSE_RECORDED,
                    entity_type="ledger_entry",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.entry_id,
                    entity_ref=stored.reference_no,
                    summary={
                        "kind": "expense",
                        "amount_minor": command.amount.amount_minor,
                        "category_id": command.category_id,
                    },
                )
            )

        assert stored.reference_no is not None
        return RecordExpenseResult(
            entry_id=stored.entry_id, reference_no=stored.reference_no, overspent=overspent
        )
