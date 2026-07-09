"""Annotation entity: optional, private (staff-only) free text on a ledger entry.

Annotations are the only place staff free text lives (context **notes** and
required **reversal reasons**). They are append-only except for a single
controlled mutation: **redaction**, which overwrites the content with a tombstone
to remove donor identity a human entered by mistake (privacy outranks
immutability). See ``docs/BUSINESS_RULES.md`` §6-8 and
``docs/adr/0009-public-private-and-pii-erasure.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from donation_bot.domain.errors import DomainError


class AnnotationType(str, Enum):
    NOTE = "note"
    REVERSAL_REASON = "reversal_reason"


# The text left behind after a PII redaction. It intentionally carries no
# information about what was removed.
REDACTION_TOMBSTONE = "[redacted: donor identity removed]"


@dataclass(frozen=True, slots=True)
class Annotation:
    entry_id: str
    annotation_type: AnnotationType
    author_id: str
    content: str
    created_at: datetime
    annotation_id: str | None = None
    redacted_at: datetime | None = None
    redacted_by: str | None = None

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise DomainError("annotation requires an entry_id")
        if not self.author_id:
            raise DomainError("annotation requires an author_id")
        if not self.is_redacted and not (self.content and self.content.strip()):
            raise DomainError("annotation content must be non-empty")
        if self.created_at.tzinfo is None:
            raise DomainError("created_at must be timezone-aware (UTC)")

    @property
    def is_redacted(self) -> bool:
        return self.redacted_at is not None

    def redact(self, *, redacted_by: str, at: datetime) -> Annotation:
        """Return a redacted copy whose content is replaced by the tombstone.

        Genuinely removes the text (privacy), never touches financial data.
        """
        if not redacted_by:
            raise DomainError("redacted_by is required")
        if at.tzinfo is None:
            raise DomainError("redaction time must be timezone-aware (UTC)")
        return replace(
            self,
            content=REDACTION_TOMBSTONE,
            redacted_at=at,
            redacted_by=redacted_by,
        )
