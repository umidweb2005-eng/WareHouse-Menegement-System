"""In-memory repository implementations over :class:`InMemoryStore`."""

from __future__ import annotations

from dataclasses import replace

from donation_bot.adapters.inmemory.store import InMemoryStore
from donation_bot.application.audit.models import AuditEntry
from donation_bot.application.ports.repositories import (
    AnnotationRepository,
    AuditLogRepository,
    LedgerRepository,
)
from donation_bot.domain.annotations.entities import Annotation
from donation_bot.domain.ledger.entities import LedgerEntry, Reversal


class InMemoryLedgerRepository(LedgerRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def add_entry(self, entry: LedgerEntry) -> LedgerEntry:
        if entry.entry_id is None:
            raise ValueError("entry must have an entry_id before persistence")
        stored = replace(entry, reference_no=self._store.next_reference())
        self._store.entries[stored.entry_id] = stored
        self._store.reference_index[stored.reference_no] = ("original", stored.entry_id)
        return stored

    def add_reversal(self, reversal: Reversal) -> Reversal:
        if reversal.entry_id is None:
            raise ValueError("reversal must have an entry_id before persistence")
        original_id = reversal.original.entry_id
        if original_id is None:
            raise ValueError("reversal target must be persisted")
        stored = replace(reversal, reference_no=self._store.next_reference())
        self._store.reversals[stored.entry_id] = stored
        self._store.reference_index[stored.reference_no] = ("reversal", stored.entry_id)
        self._store.reversed_original_ids.add(original_id)
        return stored

    def get_original(self, entry_id: str) -> LedgerEntry | None:
        return self._store.entries.get(entry_id)

    def get_original_by_reference(self, reference_no: int) -> LedgerEntry | None:
        indexed = self._store.reference_index.get(reference_no)
        if indexed is None or indexed[0] != "original":
            return None
        return self._store.entries.get(indexed[1])

    def is_reversed(self, entry_id: str) -> bool:
        return entry_id in self._store.reversed_original_ids


class InMemoryAnnotationRepository(AnnotationRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def add(self, annotation: Annotation) -> Annotation:
        if annotation.annotation_id is None:
            raise ValueError("annotation must have an id before persistence")
        self._store.annotations[annotation.annotation_id] = annotation
        return annotation

    def get(self, annotation_id: str) -> Annotation | None:
        return self._store.annotations.get(annotation_id)

    def replace(self, annotation: Annotation) -> None:
        if annotation.annotation_id is None or annotation.annotation_id not in self._store.annotations:
            raise ValueError("cannot replace an unknown annotation")
        self._store.annotations[annotation.annotation_id] = annotation

    def list_for_entry(self, entry_id: str) -> tuple[Annotation, ...]:
        return tuple(a for a in self._store.annotations.values() if a.entry_id == entry_id)


class InMemoryAuditLogRepository(AuditLogRepository):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def add(self, entry: AuditEntry) -> AuditEntry:
        stored = entry if entry.audit_id else replace(entry, audit_id=self._store.next_audit_id())
        self._store.audit.append(stored)
        return stored
