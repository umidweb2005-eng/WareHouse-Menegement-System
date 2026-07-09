"""Composition root: wire concrete adapters to the application use cases.

This is the only place that knows which backend is in use. For now it wires the
**in-memory** backend so the bot runs end-to-end without a database; swapping in
the SQLAlchemy adapters later means changing only this file — the use cases and
handlers are untouched (the whole point of the hexagonal design).

This module has no aiogram dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from donation_bot.adapters.inmemory import (
    InMemoryAuditLogRepository,
    InMemoryDonationAccountRepository,
    InMemoryLedgerReadModel,
    InMemoryStaffRepository,
    InMemoryStore,
    uow_factory,
)
from donation_bot.application.annotations.add_annotation import AddAnnotation
from donation_bot.application.annotations.redact_annotation import RedactAnnotation
from donation_bot.application.access.register_staff import RegisterStaff
from donation_bot.application.audit.query_audit_log import QueryAuditLog
from donation_bot.application.bootstrap import ensure_seed
from donation_bot.application.donations.record_donation import RecordDonation
from donation_bot.application.expenses.record_expense import RecordExpense
from donation_bot.application.ledger.list_recent_entries import ListRecentEntries
from donation_bot.application.ledger.reverse_entry import ReverseEntry
from donation_bot.application.ports.clock import Clock
from donation_bot.application.ports.ids import IdGenerator
from donation_bot.application.ports.settings import LedgerLimits, SettingsProvider
from donation_bot.application.reports.service import ReportService
from donation_bot.application.settings.configure_account import (
    ConfigureDonationAccount,
    GetActiveDonationAccount,
)
from donation_bot.adapters.inmemory.settings import StaticSettingsProvider
from donation_bot.infrastructure.clock import SystemClock
from donation_bot.infrastructure.config import Settings
from donation_bot.infrastructure.ids import UuidGenerator
from donation_bot.infrastructure.i18n.translator import Translator, get_translator


@dataclass
class Container:
    """Holds everything the Telegram adapter needs to serve a request."""

    settings: Settings
    translator: Translator
    clock: Clock
    ids: IdGenerator
    settings_provider: SettingsProvider
    staff_repo: InMemoryStaffRepository
    uow_factory: object  # Callable[[], UnitOfWork]
    # use cases
    record_donation: RecordDonation
    record_expense: RecordExpense
    reverse_entry: ReverseEntry
    list_recent_entries: ListRecentEntries
    add_annotation: AddAnnotation
    redact_annotation: RedactAnnotation
    register_staff: RegisterStaff
    configure_account: ConfigureDonationAccount
    get_active_account: GetActiveDonationAccount
    query_audit_log: QueryAuditLog
    reports: ReportService

    def seed(self) -> None:
        """Idempotently ensure the system actor and first Super Admin exist."""
        ensure_seed(
            self.uow_factory,
            self.clock,
            self.ids,
            first_super_admin_telegram_id=self.settings.bootstrap.first_super_admin_telegram_id,
            first_super_admin_name=self.settings.bootstrap.first_super_admin_name,
        )


def build_container(settings: Settings) -> Container:
    """Build the container using the in-memory backend."""
    store = InMemoryStore()
    clock = SystemClock()
    ids = UuidGenerator()
    settings_provider = StaticSettingsProvider(
        LedgerLimits(
            amount_max_minor=10_000_000_000,
            backdate_window_days=30,
            block_overspend=False,
        ),
        org_timezone=settings.app.org_timezone,
    )
    read_model = InMemoryLedgerReadModel(store)
    factory = uow_factory(store)
    staff_repo = InMemoryStaffRepository(store)
    account_repo = InMemoryDonationAccountRepository(store)
    audit_repo = InMemoryAuditLogRepository(store)

    return Container(
        settings=settings,
        translator=get_translator(settings.app.default_locale),
        clock=clock,
        ids=ids,
        settings_provider=settings_provider,
        staff_repo=staff_repo,
        uow_factory=factory,
        record_donation=RecordDonation(factory, clock, ids, settings_provider),
        record_expense=RecordExpense(factory, clock, ids, settings_provider, read_model),
        reverse_entry=ReverseEntry(factory, clock, ids),
        list_recent_entries=ListRecentEntries(read_model),
        add_annotation=AddAnnotation(factory, clock, ids),
        redact_annotation=RedactAnnotation(factory, clock),
        register_staff=RegisterStaff(factory, clock, ids),
        configure_account=ConfigureDonationAccount(factory, clock, ids),
        get_active_account=GetActiveDonationAccount(account_repo),
        query_audit_log=QueryAuditLog(audit_repo),
        reports=ReportService(read_model, clock, settings_provider),
    )
