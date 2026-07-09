"""Use case: add a private (staff-only) annotation to an entry (BR-N)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import ANNOTATION_ADDED, AuditEntry
from donation_bot.application.errors import EntryNotFoundError
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.annotations.entities import Annotation, AnnotationType


@dataclass(frozen=True, slots=True)
class AddAnnotationCommand:
    actor: StaffUser
    reference_no: int
    text: str


@dataclass(frozen=True, slots=True)
class AddAnnotationResult:
    annotation_id: str


class AddAnnotation:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = id_generator

    def execute(self, command: AddAnnotationCommand) -> AddAnnotationResult:
        require_permission(command.actor, Permission.ENTRY_ANNOTATE)
        now = self._clock.now()
        with self._uow_factory() as uow:
            entry = uow.ledger.get_original_by_reference(command.reference_no)
            if entry is None:
                raise EntryNotFoundError(f"no entry with reference {command.reference_no}")
            assert entry.entry_id is not None
            stored = uow.annotations.add(
                Annotation(
                    entry_id=entry.entry_id,
                    annotation_type=AnnotationType.NOTE,
                    author_id=command.actor.user_id,
                    content=command.text,  # domain rejects empty content
                    created_at=now,
                    annotation_id=self._ids.new_id(),
                )
            )
            uow.audit.add(
                AuditEntry(
                    action=ANNOTATION_ADDED,
                    entity_type="annotation",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=stored.annotation_id,
                    entity_ref=entry.reference_no,
                    summary={"annotation_type": AnnotationType.NOTE.value},  # never the content
                )
            )
        assert stored.annotation_id is not None
        return AddAnnotationResult(annotation_id=stored.annotation_id)
