"""Repository ports (write/lookup side).

Reads for reporting go through :mod:`donation_bot.application.ports.read_model`.
Implementations live in ``adapters`` (in-memory now; SQLAlchemy later) and must
honor the mutability matrix (append-only entries; redaction-only annotation
updates) — see ``docs/DATABASE_DESIGN.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from donation_bot.application.audit.models import AuditEntry
from donation_bot.domain.annotations.entities import Annotation
from donation_bot.domain.ledger.entities import LedgerEntry, Reversal


class LedgerRepository(ABC):
    @abstractmethod
    def add_entry(self, entry: LedgerEntry) -> LedgerEntry:
        """Persist an original entry, assigning and returning its reference_no."""

    @abstractmethod
    def add_reversal(self, reversal: Reversal) -> Reversal:
        """Persist a reversal, assigning and returning its reference_no."""

    @abstractmethod
    def get_original(self, entry_id: str) -> LedgerEntry | None: ...

    @abstractmethod
    def get_original_by_reference(self, reference_no: int) -> LedgerEntry | None: ...

    @abstractmethod
    def is_reversed(self, entry_id: str) -> bool:
        """Whether an original already has a reversal (enforces BR-L3)."""


class AnnotationRepository(ABC):
    @abstractmethod
    def add(self, annotation: Annotation) -> Annotation:
        """Persist a new annotation, assigning and returning its id."""

    @abstractmethod
    def get(self, annotation_id: str) -> Annotation | None: ...

    @abstractmethod
    def replace(self, annotation: Annotation) -> None:
        """Overwrite an existing annotation in place (used only for redaction)."""

    @abstractmethod
    def list_for_entry(self, entry_id: str) -> tuple[Annotation, ...]: ...


class AuditLogRepository(ABC):
    @abstractmethod
    def add(self, entry: AuditEntry) -> AuditEntry:
        """Append an audit entry, assigning and returning its id."""
