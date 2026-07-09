"""In-memory Unit of Work with snapshot-based rollback.

On a clean exit the writes made during the block are kept; if the block raises,
the store is restored to its pre-transaction snapshot, giving true atomicity for
the entry+audit write (BR-C1) so tests can verify that a failure persists neither.
"""

from __future__ import annotations

from donation_bot.adapters.inmemory.repositories import (
    InMemoryAnnotationRepository,
    InMemoryAuditLogRepository,
    InMemoryDonationAccountRepository,
    InMemoryLedgerRepository,
    InMemoryStaffRepository,
)
from donation_bot.adapters.inmemory.store import InMemoryStore, _Snapshot
from donation_bot.application.ports.unit_of_work import UnitOfWork


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self.ledger = InMemoryLedgerRepository(store)
        self.annotations = InMemoryAnnotationRepository(store)
        self.audit = InMemoryAuditLogRepository(store)
        self.staff = InMemoryStaffRepository(store)
        self.accounts = InMemoryDonationAccountRepository(store)
        self._snapshot: _Snapshot | None = None

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._snapshot = self._store.snapshot()
        return self

    def commit(self) -> None:
        # Writes were applied in place; accept them and drop the snapshot.
        self._snapshot = None

    def rollback(self) -> None:
        if self._snapshot is not None:
            self._store.restore(self._snapshot)
            self._snapshot = None


def uow_factory(store: InMemoryStore):
    """Return a factory that creates a fresh Unit of Work bound to ``store``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    return factory
