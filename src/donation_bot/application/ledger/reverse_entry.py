"""Use case: reverse (correct) a ledger entry (BR-L2/BR-L3).

Posts an adjustment whose amount is derived from the original. The required reason
is stored as a private ``reversal_reason`` annotation (redactable), never on the
immutable row and never copied into the audit log (BR-AU2/BR-X4).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import ENTRY_REVERSED, AuditEntry
from donation_bot.application.errors import AlreadyReversedError, EntryNotFoundError
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.annotations.entities import Annotation, AnnotationType
from donation_bot.domain.ledger.entities import EntryKind


@dataclass(frozen=True, slots=True)
class ReverseEntryCommand:
    actor: StaffUser
    reference_no: int  # the original entry's public reference
    reason: str


@dataclass(frozen=True, slots=True)
class ReverseEntryResult:
    reversal_entry_id: str
    reversal_reference_no: int
    original_reference_no: int


_REVERSE_PERMISSION = {
    EntryKind.DONATION: Permission.DONATION_REVERSE,
    EntryKind.EXPENSE: Permission.EXPENSE_REVERSE,
}


class ReverseEntry:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator

    def execute(self, command: ReverseEntryCommand) -> ReverseEntryResult:
        now = self._clock.now()
        with self._uow_factory() as uow:
            original = uow.ledger.get_original_by_reference(command.reference_no)
            if original is None:
                raise EntryNotFoundError(f"no original entry with reference {command.reference_no}")

            # Permission depends on what is being corrected.
            require_permission(command.actor, _REVERSE_PERMISSION[original.kind])

            assert original.entry_id is not None
            if uow.ledger.is_reversed(original.entry_id):
                raise AlreadyReversedError(
                    f"entry {command.reference_no} was already corrected"
                )

            # Domain validates the reason and derives the amount/effect.
            reversal = original.reverse(reason=command.reason, recorded_by=command.actor.user_id)
            reversal = replace(reversal, entry_id=self._ids.new_id(), recorded_at=now)
            stored = uow.ledger.add_reversal(reversal)

            # The reason lives in a private, redactable annotation (not on the row,
            # not duplicated into audit).
            uow.annotations.add(
                Annotation(
                    entry_id=stored.entry_id,
                    annotation_type=AnnotationType.REVERSAL_REASON,
                    author_id=command.actor.user_id,
                    content=command.reason,
                    created_at=now,
                    annotation_id=self._ids.new_id(),
                )
            )
            uow.audit.add(
                AuditEntry(
                    action=ENTRY_REVERSED,
                    entity_type="ledger_entry",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.entry_id,
                    entity_ref=stored.reference_no,
                    summary={
                        "reverses_reference": original.reference_no,
                        "kind": original.kind.value,
                    },
                )
            )

        assert stored.reference_no is not None
        assert original.reference_no is not None
        return ReverseEntryResult(
            reversal_entry_id=stored.entry_id,
            reversal_reference_no=stored.reference_no,
            original_reference_no=original.reference_no,
        )
