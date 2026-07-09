"""Use case: record a received donation (BR-D)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import DONATION_RECORDED, AuditEntry
from donation_bot.application.ledger.validation import validate_amount, validate_event_time
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.settings import SettingsProvider
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.annotations.entities import Annotation, AnnotationType
from donation_bot.domain.ledger.entities import DonationSource, record_donation
from donation_bot.domain.money import Money


@dataclass(frozen=True, slots=True)
class RecordDonationCommand:
    actor: StaffUser
    amount: Money
    source: DonationSource
    event_at: datetime
    note: str | None = None  # optional PRIVATE annotation (staff-only)


@dataclass(frozen=True, slots=True)
class RecordDonationResult:
    entry_id: str
    reference_no: int


class RecordDonation:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
        settings: SettingsProvider,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator
        self._settings = settings

    def execute(self, command: RecordDonationCommand) -> RecordDonationResult:
        require_permission(command.actor, Permission.DONATION_RECORD)

        limits = self._settings.ledger_limits()
        now = self._clock.now()
        validate_amount(command.amount, limits)
        validate_event_time(command.event_at, now, limits)

        entry = record_donation(
            amount=command.amount,
            source=command.source,
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
                    action=DONATION_RECORDED,
                    entity_type="ledger_entry",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.entry_id,
                    entity_ref=stored.reference_no,
                    summary={
                        "kind": "donation",
                        "amount_minor": command.amount.amount_minor,
                        "source": command.source.value,
                    },
                )
            )

        assert stored.reference_no is not None  # assigned by the repository
        return RecordDonationResult(entry_id=stored.entry_id, reference_no=stored.reference_no)
