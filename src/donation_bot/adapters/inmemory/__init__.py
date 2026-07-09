"""In-memory adapters implementing the application ports.

These are real, dependency-free implementations (usable for local/dev runs and as
test doubles). They let the entire application layer be exercised without a
database or any third-party package.
"""

from donation_bot.adapters.inmemory.clock import ManualClock
from donation_bot.adapters.inmemory.ids import SequentialIdGenerator
from donation_bot.adapters.inmemory.read_model import InMemoryLedgerReadModel
from donation_bot.adapters.inmemory.repositories import (
    InMemoryAnnotationRepository,
    InMemoryAuditLogRepository,
    InMemoryDonationAccountRepository,
    InMemoryLedgerRepository,
    InMemoryStaffRepository,
)
from donation_bot.adapters.inmemory.settings import StaticSettingsProvider
from donation_bot.adapters.inmemory.store import InMemoryStore
from donation_bot.adapters.inmemory.unit_of_work import InMemoryUnitOfWork, uow_factory

__all__ = [
    "ManualClock",
    "SequentialIdGenerator",
    "InMemoryLedgerReadModel",
    "InMemoryLedgerRepository",
    "InMemoryAnnotationRepository",
    "InMemoryAuditLogRepository",
    "InMemoryStaffRepository",
    "InMemoryDonationAccountRepository",
    "StaticSettingsProvider",
    "InMemoryStore",
    "InMemoryUnitOfWork",
    "uow_factory",
]
