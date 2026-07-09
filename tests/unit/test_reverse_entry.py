"""ReverseEntry use-case tests."""

from __future__ import annotations

import unittest

import _appsupport as app

from donation_bot.application.audit.models import ENTRY_REVERSED
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import (
    AlreadyReversedError,
    EntryNotFoundError,
    PermissionDeniedError,
)
from donation_bot.application.ledger.reverse_entry import ReverseEntryCommand
from donation_bot.domain.annotations.entities import AnnotationType
from donation_bot.domain.errors import ReversalError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money


class ReverseEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def _donate(self, minor=500000):
        return self.ctx.record_donation.execute(
            RecordDonationCommand(
                actor=self.ctx.treasurer,
                amount=Money(minor),
                source=DonationSource.CASH,
                event_at=self.ctx.clock.now(),
            )
        )

    def test_reversal_nets_balance_to_zero(self) -> None:
        donation = self._donate(500000)
        self.assertEqual(self.ctx.read_model.totals(None).net, Money(500000))
        result = self.ctx.reverse_entry.execute(
            ReverseEntryCommand(
                actor=self.ctx.treasurer, reference_no=donation.reference_no, reason="entered twice"
            )
        )
        self.assertEqual(result.original_reference_no, donation.reference_no)
        self.assertEqual(self.ctx.read_model.totals(None).net, Money(0))

    def test_reason_stored_as_private_annotation_not_in_audit(self) -> None:
        donation = self._donate()
        reason = "duplicate of gift by Ali"  # accidental identity in reason
        self.ctx.reverse_entry.execute(
            ReverseEntryCommand(
                actor=self.ctx.treasurer, reference_no=donation.reference_no, reason=reason
            )
        )
        reason_anns = [
            a
            for a in self.ctx.store.annotations.values()
            if a.annotation_type is AnnotationType.REVERSAL_REASON
        ]
        self.assertEqual(len(reason_anns), 1)
        self.assertEqual(reason_anns[0].content, reason)
        # audit records the reversal but never the reason text
        reversed_audits = [e for e in self.ctx.store.audit if e.action == ENTRY_REVERSED]
        self.assertEqual(len(reversed_audits), 1)
        self.assertNotIn(reason, str(reversed_audits[0].summary))

    def test_cannot_reverse_twice(self) -> None:
        donation = self._donate()
        self.ctx.reverse_entry.execute(
            ReverseEntryCommand(actor=self.ctx.treasurer, reference_no=donation.reference_no, reason="x")
        )
        with self.assertRaises(AlreadyReversedError):
            self.ctx.reverse_entry.execute(
                ReverseEntryCommand(
                    actor=self.ctx.treasurer, reference_no=donation.reference_no, reason="again"
                )
            )

    def test_unknown_reference_raises(self) -> None:
        with self.assertRaises(EntryNotFoundError):
            self.ctx.reverse_entry.execute(
                ReverseEntryCommand(actor=self.ctx.treasurer, reference_no=999, reason="x")
            )

    def test_empty_reason_rejected(self) -> None:
        donation = self._donate()
        with self.assertRaises(ReversalError):
            self.ctx.reverse_entry.execute(
                ReverseEntryCommand(
                    actor=self.ctx.treasurer, reference_no=donation.reference_no, reason="  "
                )
            )

    def test_permission_denied_for_non_treasurer(self) -> None:
        donation = self._donate()
        with self.assertRaises(PermissionDeniedError):
            self.ctx.reverse_entry.execute(
                ReverseEntryCommand(
                    actor=self.ctx.plain_user, reference_no=donation.reference_no, reason="x"
                )
            )
        self.assertFalse(self.ctx.read_model.totals(None).net == Money(0))  # unchanged


if __name__ == "__main__":
    unittest.main()
