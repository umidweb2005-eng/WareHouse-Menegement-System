"""Shared wiring for application-layer unit tests (in-memory adapters).

Not a test module (no ``test_`` prefix). Provides a fully wired set of use cases
over in-memory adapters plus helpers to seed the ledger directly (bypassing
use-case validation) when a test needs arbitrary event times.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from donation_bot.adapters.inmemory import (
    InMemoryDonationAccountRepository,
    InMemoryLedgerReadModel,
    InMemoryLedgerRepository,
    InMemoryStaffRepository,
    InMemoryStore,
    ManualClock,
    SequentialIdGenerator,
    StaticSettingsProvider,
    uow_factory,
)
from donation_bot.application.access.register_staff import RegisterStaff
from donation_bot.application.annotations.add_annotation import AddAnnotation
from donation_bot.application.annotations.redact_annotation import RedactAnnotation
from donation_bot.application.donations.record_donation import RecordDonation
from donation_bot.application.expenses.record_expense import RecordExpense
from donation_bot.application.ledger.reverse_entry import ReverseEntry
from donation_bot.application.ports.settings import LedgerLimits
from donation_bot.application.reports.service import ReportService
from donation_bot.application.settings.configure_account import (
    ConfigureDonationAccount,
    GetActiveDonationAccount,
)
from donation_bot.domain.access.entities import (
    SUPER_ADMIN_ROLE,
    TREASURER_ROLE,
    USER_ROLE,
    StaffUser,
)
from donation_bot.domain.ledger.entities import (
    DonationSource,
    LedgerEntry,
    record_donation,
    record_expense,
)
from donation_bot.domain.money import Money

DEFAULT_NOW = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)


def build(
    *,
    now: datetime = DEFAULT_NOW,
    block_overspend: bool = False,
    org_timezone: str = "Asia/Tashkent",
    amount_max_minor: int = 10_000_000_000,
    backdate_window_days: int = 30,
) -> SimpleNamespace:
    store = InMemoryStore()
    clock = ManualClock(now)
    ids = SequentialIdGenerator()
    settings = StaticSettingsProvider(
        LedgerLimits(
            amount_max_minor=amount_max_minor,
            backdate_window_days=backdate_window_days,
            block_overspend=block_overspend,
        ),
        org_timezone=org_timezone,
    )
    read_model = InMemoryLedgerReadModel(store)
    factory = uow_factory(store)

    return SimpleNamespace(
        store=store,
        clock=clock,
        ids=ids,
        settings=settings,
        read_model=read_model,
        uow_factory=factory,
        ledger_repo=InMemoryLedgerRepository(store),
        staff_repo=InMemoryStaffRepository(store),
        account_repo=InMemoryDonationAccountRepository(store),
        # use cases
        record_donation=RecordDonation(factory, clock, ids, settings),
        record_expense=RecordExpense(factory, clock, ids, settings, read_model),
        reverse_entry=ReverseEntry(factory, clock, ids),
        add_annotation=AddAnnotation(factory, clock, ids),
        redact_annotation=RedactAnnotation(factory, clock),
        register_staff=RegisterStaff(factory, clock, ids),
        configure_account=ConfigureDonationAccount(factory, clock, ids),
        get_active_account=GetActiveDonationAccount(InMemoryDonationAccountRepository(store)),
        reports=ReportService(read_model, clock, settings),
        # actors
        treasurer=StaffUser(
            user_id="tre-1", telegram_id=1001, roles=frozenset({TREASURER_ROLE}), display_name="T"
        ),
        admin=StaffUser(
            user_id="adm-1", telegram_id=1002, roles=frozenset({SUPER_ADMIN_ROLE}), display_name="A"
        ),
        plain_user=StaffUser(user_id="usr-1", telegram_id=1003, roles=frozenset({USER_ROLE})),
    )


# --- direct seeding helpers (bypass use-case validation, for read-side tests) ---
def seed_donation(ctx: SimpleNamespace, minor: int, event_at: datetime) -> LedgerEntry:
    entry = record_donation(
        amount=Money(minor),
        source=DonationSource.CASH,
        event_at=event_at,
        recorded_by="tre-1",
        entry_id=ctx.ids.new_id(),
        recorded_at=event_at,
    )
    return ctx.ledger_repo.add_entry(entry)


def seed_expense(
    ctx: SimpleNamespace, minor: int, event_at: datetime, *, category_id: int = 1, description: str = "Aid"
) -> LedgerEntry:
    entry = record_expense(
        amount=Money(minor),
        category_id=category_id,
        description=description,
        event_at=event_at,
        recorded_by="tre-1",
        entry_id=ctx.ids.new_id(),
        recorded_at=event_at,
    )
    return ctx.ledger_repo.add_entry(entry)


def seed_reversal(ctx: SimpleNamespace, original: LedgerEntry, reason: str = "correction") -> None:
    from dataclasses import replace

    reversal = original.reverse(reason=reason, recorded_by="tre-1")
    reversal = replace(reversal, entry_id=ctx.ids.new_id(), recorded_at=original.event_at)
    ctx.ledger_repo.add_reversal(reversal)
