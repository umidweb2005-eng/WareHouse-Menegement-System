"""Unit of Work port: a single atomic transaction boundary (BR-C1).

Groups the write repositories so a use case commits an entry and its audit record
together (or neither). Used as a context manager: it commits on clean exit and
rolls back if the body raises.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from donation_bot.application.ports.repositories import (
    AnnotationRepository,
    AuditLogRepository,
    LedgerRepository,
)


class UnitOfWork(ABC):
    ledger: LedgerRepository
    annotations: AnnotationRepository
    audit: AuditLogRepository

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        return False  # never suppress exceptions

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
