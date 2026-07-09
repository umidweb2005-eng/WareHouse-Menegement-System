"""Use case: redact leaked donor identity from an annotation (BR-X, PII-erasure).

The single permitted content mutation. It overwrites the free text with a
tombstone, never touches financial fields, and audits the event **without**
copying the leaked text.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.audit.models import ANNOTATION_REDACTED, AuditEntry
from donation_bot.application.errors import AnnotationNotFoundError
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.unit_of_work import UnitOfWork
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission


@dataclass(frozen=True, slots=True)
class RedactAnnotationCommand:
    actor: StaffUser
    annotation_id: str


@dataclass(frozen=True, slots=True)
class RedactAnnotationResult:
    annotation_id: str


class RedactAnnotation:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def execute(self, command: RedactAnnotationCommand) -> RedactAnnotationResult:
        require_permission(command.actor, Permission.PII_ERASE)
        now = self._clock.now()
        with self._uow_factory() as uow:
            annotation = uow.annotations.get(command.annotation_id)
            if annotation is None:
                raise AnnotationNotFoundError(f"no annotation {command.annotation_id}")
            redacted = annotation.redact(redacted_by=command.actor.user_id, at=now)
            uow.annotations.replace(redacted)
            uow.audit.add(
                AuditEntry(
                    action=ANNOTATION_REDACTED,
                    entity_type="annotation",
                    actor_user_id=command.actor.user_id,
                    created_at=now,
                    entity_id=command.annotation_id,
                    # Deliberately NO content copied into the audit record (BR-X4).
                    summary={"annotation_type": annotation.annotation_type.value},
                )
            )
        return RedactAnnotationResult(annotation_id=command.annotation_id)
