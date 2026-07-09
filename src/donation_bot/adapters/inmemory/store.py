"""Shared in-memory storage backing the in-memory adapters.

Holds ledger entries, reversals, annotations, and the audit log, plus the
reference-number sequence. Supports ``snapshot``/``restore`` so the in-memory Unit
of Work can roll back on error (needed to verify write atomicity, BR-C1).

Entities are immutable (frozen dataclasses), so shallow copies of the containers
are sufficient for a correct snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from donation_bot.application.audit.models import AuditEntry
from donation_bot.domain.annotations.entities import Annotation
from donation_bot.domain.ledger.entities import LedgerEntry, Reversal


@dataclass
class _Snapshot:
    entries: dict[str, LedgerEntry]
    reversals: dict[str, Reversal]
    reference_index: dict[int, tuple[str, str]]
    reversed_original_ids: set[str]
    annotations: dict[str, Annotation]
    audit: list[AuditEntry]
    ref_seq: int
    audit_seq: int


@dataclass
class InMemoryStore:
    entries: dict[str, LedgerEntry] = field(default_factory=dict)  # entry_id -> original
    reversals: dict[str, Reversal] = field(default_factory=dict)  # entry_id -> reversal
    reference_index: dict[int, tuple[str, str]] = field(default_factory=dict)  # ref -> (role, id)
    reversed_original_ids: set[str] = field(default_factory=set)
    annotations: dict[str, Annotation] = field(default_factory=dict)
    audit: list[AuditEntry] = field(default_factory=list)
    _ref_seq: int = 0
    _audit_seq: int = 0

    def next_reference(self) -> int:
        self._ref_seq += 1
        return self._ref_seq

    def next_audit_id(self) -> str:
        self._audit_seq += 1
        return f"audit-{self._audit_seq}"

    def snapshot(self) -> _Snapshot:
        return _Snapshot(
            entries=dict(self.entries),
            reversals=dict(self.reversals),
            reference_index=dict(self.reference_index),
            reversed_original_ids=set(self.reversed_original_ids),
            annotations=dict(self.annotations),
            audit=list(self.audit),
            ref_seq=self._ref_seq,
            audit_seq=self._audit_seq,
        )

    def restore(self, snap: _Snapshot) -> None:
        self.entries = dict(snap.entries)
        self.reversals = dict(snap.reversals)
        self.reference_index = dict(snap.reference_index)
        self.reversed_original_ids = set(snap.reversed_original_ids)
        self.annotations = dict(snap.annotations)
        self.audit = list(snap.audit)
        self._ref_seq = snap.ref_seq
        self._audit_seq = snap.audit_seq
