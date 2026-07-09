"""Ledger entity tests (invariants I2/I3: immutability + derived reversals)."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from donation_bot.domain.errors import InvalidLedgerEntryError, ReversalError
from donation_bot.domain.ledger.entities import (
    DonationSource,
    EntryKind,
    EntryRole,
    LedgerEntry,
    Reversal,
    balance,
    is_reversed,
    record_donation,
    record_expense,
)
from donation_bot.domain.money import Money

WHEN = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)


def a_donation(amount: int = 1000, by: str = "t1") -> LedgerEntry:
    return record_donation(
        amount=Money(amount), source=DonationSource.CASH, event_at=WHEN, recorded_by=by
    )


def an_expense(amount: int = 400, by: str = "t1") -> LedgerEntry:
    return record_expense(
        amount=Money(amount),
        category_id=1,
        description="Aid to family",
        event_at=WHEN,
        recorded_by=by,
    )


class OriginalEntryTests(unittest.TestCase):
    def test_donation_is_positive_inflow(self) -> None:
        d = a_donation(1000)
        self.assertEqual(d.kind, EntryKind.DONATION)
        self.assertEqual(d.entry_role, EntryRole.ORIGINAL)
        self.assertEqual(d.signed_effective_amount, Money(1000))

    def test_expense_is_negative_outflow(self) -> None:
        e = an_expense(400)
        self.assertEqual(e.signed_effective_amount, Money(-400))

    def test_amount_must_be_positive(self) -> None:
        with self.assertRaises(InvalidLedgerEntryError):
            record_donation(
                amount=Money(0), source=DonationSource.CASH, event_at=WHEN, recorded_by="t1"
            )
        with self.assertRaises(InvalidLedgerEntryError):
            an_expense(-5)

    def test_expense_requires_nonempty_description(self) -> None:
        with self.assertRaises(InvalidLedgerEntryError):
            record_expense(
                amount=Money(100),
                category_id=1,
                description="   ",
                event_at=WHEN,
                recorded_by="t1",
            )

    def test_event_at_must_be_timezone_aware(self) -> None:
        with self.assertRaises(InvalidLedgerEntryError):
            record_donation(
                amount=Money(1),
                source=DonationSource.CASH,
                event_at=datetime(2026, 5, 1, 12, 0),  # naive
                recorded_by="t1",
            )


class ReversalTests(unittest.TestCase):
    def test_reversal_amount_is_derived_from_original(self) -> None:
        d = a_donation(1000)
        r = d.reverse(reason="entered twice", recorded_by="t2")
        self.assertEqual(r.entry_role, EntryRole.REVERSAL)
        self.assertEqual(r.amount, d.amount)  # derived, not supplied
        self.assertEqual(r.signed_effective_amount, Money(-1000))

    def test_reversal_requires_reason(self) -> None:
        d = a_donation()
        with self.assertRaises(ReversalError):
            d.reverse(reason="  ", recorded_by="t2")

    def test_a_reversal_cannot_be_reversed(self) -> None:
        # Structural guarantee: only originals expose ``reverse``.
        r = a_donation().reverse(reason="oops", recorded_by="t2")
        self.assertFalse(hasattr(r, "reverse"))

    def test_reversal_only_targets_an_original(self) -> None:
        with self.assertRaises(ReversalError):
            Reversal(original="not-an-entry", reason="x", recorded_by="t2")  # type: ignore[arg-type]


class BalanceTests(unittest.TestCase):
    def test_balance_sums_signed_amounts(self) -> None:
        entries = [a_donation(1000), a_donation(500), an_expense(400)]
        self.assertEqual(balance(entries), Money(1100))

    def test_reversed_pair_nets_to_zero(self) -> None:
        d = a_donation(1000)
        r = d.reverse(reason="duplicate", recorded_by="t2")
        self.assertEqual(balance([d, r]), Money(0))

    def test_is_reversed_by_identity_and_by_id(self) -> None:
        d = a_donation(1000)
        r = d.reverse(reason="x", recorded_by="t2")
        self.assertTrue(is_reversed(d, [r]))
        self.assertFalse(is_reversed(an_expense(400), [r]))


if __name__ == "__main__":
    unittest.main()
