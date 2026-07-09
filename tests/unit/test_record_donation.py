"""RecordDonation use-case tests."""

from __future__ import annotations

import unittest
from datetime import timedelta

import _appsupport as app

from donation_bot.application.audit.models import DONATION_RECORDED
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import (
    AmountLimitExceededError,
    InvalidEventTimeError,
    PermissionDeniedError,
)
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money


class RecordDonationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def _cmd(self, actor=None, minor=500000, note=None, event_at=None):
        return RecordDonationCommand(
            actor=actor or self.ctx.treasurer,
            amount=Money(minor),
            source=DonationSource.CASH,
            event_at=event_at or self.ctx.clock.now(),
            note=note,
        )

    def test_treasurer_records_donation(self) -> None:
        result = self.ctx.record_donation.execute(self._cmd(minor=500000))
        self.assertEqual(result.reference_no, 1)
        self.assertEqual(self.ctx.read_model.totals(None).total_in, Money(500000))
        # exactly one audit entry of the right action
        self.assertEqual(len(self.ctx.store.audit), 1)
        self.assertEqual(self.ctx.store.audit[0].action, DONATION_RECORDED)

    def test_private_note_is_stored_as_annotation_not_in_audit(self) -> None:
        secret = "from Mr. Anonymous Donor"  # a treasurer mistakenly typing identity
        result = self.ctx.record_donation.execute(self._cmd(note=secret))
        # entry_id resolves to the created donation
        entry = self.ctx.store.entries[result.entry_id]
        anns = [a for a in self.ctx.store.annotations.values() if a.entry_id == entry.entry_id]
        self.assertEqual(len(anns), 1)
        self.assertEqual(anns[0].content, secret)  # stored privately
        # the audit summary must NOT contain the note text
        self.assertNotIn(secret, str(self.ctx.store.audit[0].summary))

    def test_permission_denied_for_non_treasurer(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.record_donation.execute(self._cmd(actor=self.ctx.plain_user))
        self.assertEqual(len(self.ctx.store.entries), 0)

    def test_amount_over_max_rejected(self) -> None:
        ctx = app.build(amount_max_minor=1000)
        with self.assertRaises(AmountLimitExceededError):
            ctx.record_donation.execute(
                RecordDonationCommand(
                    actor=ctx.treasurer,
                    amount=Money(2000),
                    source=DonationSource.CASH,
                    event_at=ctx.clock.now(),
                )
            )

    def test_future_event_time_rejected(self) -> None:
        future = self.ctx.clock.now() + timedelta(days=1)
        with self.assertRaises(InvalidEventTimeError):
            self.ctx.record_donation.execute(self._cmd(event_at=future))

    def test_backdated_beyond_window_rejected(self) -> None:
        old = self.ctx.clock.now() - timedelta(days=45)  # window is 30
        with self.assertRaises(InvalidEventTimeError):
            self.ctx.record_donation.execute(self._cmd(event_at=old))

    def test_backdated_within_window_allowed(self) -> None:
        recent = self.ctx.clock.now() - timedelta(days=5)
        result = self.ctx.record_donation.execute(self._cmd(event_at=recent))
        self.assertEqual(result.reference_no, 1)


if __name__ == "__main__":
    unittest.main()
