"""RecordExpense use-case tests."""

from __future__ import annotations

import unittest

import _appsupport as app

from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import (
    OverspendError,
    PermissionDeniedError,
)
from donation_bot.application.expenses.record_expense import RecordExpenseCommand
from donation_bot.domain.errors import InvalidLedgerEntryError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money


class RecordExpenseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def _donate(self, minor: int) -> None:
        self.ctx.record_donation.execute(
            RecordDonationCommand(
                actor=self.ctx.treasurer,
                amount=Money(minor),
                source=DonationSource.CASH,
                event_at=self.ctx.clock.now(),
            )
        )

    def _expense_cmd(self, minor=300000, description="Aid to family", actor=None):
        return RecordExpenseCommand(
            actor=actor or self.ctx.treasurer,
            amount=Money(minor),
            category_id=1,
            description=description,
            event_at=self.ctx.clock.now(),
        )

    def test_records_expense_and_reduces_balance(self) -> None:
        self._donate(1000000)
        result = self.ctx.record_expense.execute(self._expense_cmd(300000))
        self.assertFalse(result.overspent)
        totals = self.ctx.read_model.totals(None)
        self.assertEqual(totals.total_out, Money(300000))
        self.assertEqual(totals.net, Money(700000))
        # public usage line is present with its description
        lines = self.ctx.read_model.expense_lines(None)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].description, "Aid to family")

    def test_overspend_warns_by_default(self) -> None:
        # no donations -> spending anything overspends, but is allowed (warn)
        result = self.ctx.record_expense.execute(self._expense_cmd(100))
        self.assertTrue(result.overspent)
        self.assertEqual(len(self.ctx.store.entries), 1)  # still recorded

    def test_overspend_blocked_when_policy_enabled(self) -> None:
        ctx = app.build(block_overspend=True)
        with self.assertRaises(OverspendError):
            ctx.record_expense.execute(
                RecordExpenseCommand(
                    actor=ctx.treasurer,
                    amount=Money(100),
                    category_id=1,
                    description="X",
                    event_at=ctx.clock.now(),
                )
            )
        self.assertEqual(len(ctx.store.entries), 0)  # nothing recorded

    def test_description_is_required(self) -> None:
        self._donate(1000)
        with self.assertRaises(InvalidLedgerEntryError):
            self.ctx.record_expense.execute(self._expense_cmd(minor=100, description="   "))

    def test_permission_denied_for_non_treasurer(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.record_expense.execute(self._expense_cmd(actor=self.ctx.plain_user))


if __name__ == "__main__":
    unittest.main()
