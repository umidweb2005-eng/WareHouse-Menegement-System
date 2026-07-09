"""Permission-enforcement and write-atomicity tests."""

from __future__ import annotations

import unittest

import _appsupport as app

from donation_bot.application.access.authorization import require_permission
from donation_bot.application.donations.record_donation import (
    RecordDonation,
    RecordDonationCommand,
)
from donation_bot.application.errors import PermissionDeniedError
from donation_bot.adapters.inmemory.unit_of_work import InMemoryUnitOfWork
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money


class RequirePermissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_public_caller_may_view_reports(self) -> None:
        require_permission(None, Permission.REPORT_VIEW)  # no raise

    def test_public_caller_may_not_record(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            require_permission(None, Permission.DONATION_RECORD)

    def test_treasurer_can_record_but_not_erase_pii(self) -> None:
        require_permission(self.ctx.treasurer, Permission.DONATION_RECORD)
        with self.assertRaises(PermissionDeniedError):
            require_permission(self.ctx.treasurer, Permission.PII_ERASE)

    def test_admin_can_erase_pii(self) -> None:
        require_permission(self.ctx.admin, Permission.PII_ERASE)


class WriteAtomicityTests(unittest.TestCase):
    def test_failure_rolls_back_entry_and_audit_together(self) -> None:
        ctx = app.build()
        store = ctx.store

        class _BoomAudit:
            def add(self, entry):  # noqa: ANN001 - test stub
                raise RuntimeError("audit failure")

        def failing_factory() -> InMemoryUnitOfWork:
            uow = InMemoryUnitOfWork(store)
            uow.audit = _BoomAudit()  # type: ignore[assignment]
            return uow

        use_case = RecordDonation(failing_factory, ctx.clock, ctx.ids, ctx.settings)
        cmd = RecordDonationCommand(
            actor=ctx.treasurer,
            amount=Money(1000),
            source=DonationSource.CASH,
            event_at=ctx.clock.now(),
        )
        with self.assertRaises(RuntimeError):
            use_case.execute(cmd)

        # The entry write must have been rolled back along with the (failed) audit.
        self.assertEqual(len(store.entries), 0)
        self.assertEqual(len(store.audit), 0)


if __name__ == "__main__":
    unittest.main()
