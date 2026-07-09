"""Tests for the ListRecentEntries use case and recent-entries formatting."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import _appsupport as app

from donation_bot.adapters.telegram.formatting import format_recent_entries
from donation_bot.application.errors import PermissionDeniedError
from donation_bot.infrastructure.i18n.translator import get_translator

UTC = timezone.utc


class ListRecentEntriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_newest_first_with_reversed_flag(self) -> None:
        d1 = app.seed_donation(self.ctx, 1000, datetime(2026, 5, 1, 8, 0, tzinfo=UTC))
        app.seed_expense(self.ctx, 400, datetime(2026, 5, 2, 8, 0, tzinfo=UTC))
        app.seed_reversal(self.ctx, d1, reason="mistake")

        entries = self.ctx.list_recent_entries.execute(self.ctx.treasurer)
        # originals only (2), newest first by reference_no
        self.assertEqual(len(entries), 2)
        self.assertGreater(entries[0].reference_no, entries[1].reference_no)
        # the reversed donation is flagged
        by_ref = {e.reference_no: e for e in entries}
        self.assertTrue(by_ref[d1.reference_no].is_reversed)

    def test_limit_respected(self) -> None:
        for i in range(5):
            app.seed_donation(self.ctx, 100, datetime(2026, 5, 1, 8, i, tzinfo=UTC))
        self.assertEqual(len(self.ctx.list_recent_entries.execute(self.ctx.admin, limit=3)), 3)

    def test_public_and_plain_user_denied(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.list_recent_entries.execute(None)
        with self.assertRaises(PermissionDeniedError):
            self.ctx.list_recent_entries.execute(self.ctx.plain_user)


class FormatRecentEntriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()
        self.tr = get_translator("uz")

    def test_empty(self) -> None:
        text = format_recent_entries((), self.tr, "Asia/Tashkent")
        self.assertIn(self.tr.t("recent.empty"), text)

    def test_lists_donation_and_expense_with_dates(self) -> None:
        app.seed_donation(self.ctx, 500000, datetime(2026, 5, 10, 8, 0, tzinfo=UTC))
        app.seed_expense(self.ctx, 300000, datetime(2026, 5, 11, 8, 0, tzinfo=UTC), description="Svet")
        entries = self.ctx.list_recent_entries.execute(self.ctx.treasurer)
        text = format_recent_entries(entries, self.tr, "Asia/Tashkent")
        self.assertIn("5 000 so'm", text)
        self.assertIn("3 000 so'm", text)
        self.assertIn("Svet", text)  # public expense description shown
        self.assertIn("10.05.2026", text)


if __name__ == "__main__":
    unittest.main()
