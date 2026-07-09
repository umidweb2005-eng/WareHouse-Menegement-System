"""Report & statistics tests (derived, reproducible, timezone-correct)."""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

import _appsupport as app

from donation_bot.domain.money import Money

UTC = timezone.utc


class ReportTotalsTests(unittest.TestCase):
    def setUp(self) -> None:
        # "now" in mid-May 2026; seeding bypasses back-date validation.
        self.ctx = app.build(now=datetime(2026, 5, 15, 12, 0, tzinfo=UTC))
        app.seed_donation(self.ctx, 1_000_000, datetime(2026, 5, 10, 8, 0, tzinfo=UTC))
        app.seed_donation(self.ctx, 500_000, datetime(2026, 5, 15, 12, 0, tzinfo=UTC))
        app.seed_expense(self.ctx, 300_000, datetime(2026, 5, 15, 12, 0, tzinfo=UTC), description="Aid")
        app.seed_donation(self.ctx, 200_000, datetime(2026, 4, 20, 8, 0, tzinfo=UTC))
        reversed_one = app.seed_donation(self.ctx, 999_999, datetime(2026, 5, 1, 8, 0, tzinfo=UTC))
        app.seed_reversal(self.ctx, reversed_one, reason="mistake")

    def test_all_time_totals_exclude_reversed(self) -> None:
        r = self.ctx.reports.total_report()
        self.assertEqual(r.totals.total_in, Money(1_700_000))  # 999_999 reversed excluded
        self.assertEqual(r.totals.total_out, Money(300_000))
        self.assertEqual(r.totals.net, Money(1_400_000))
        self.assertEqual(r.totals.donation_count, 3)
        self.assertEqual(r.totals.expense_count, 1)

    def test_monthly_report_only_includes_that_month(self) -> None:
        r = self.ctx.reports.monthly_report(2026, 5)
        self.assertEqual(r.totals.total_in, Money(1_500_000))  # April 200k excluded
        self.assertEqual(r.totals.net, Money(1_200_000))

    def test_daily_report(self) -> None:
        r = self.ctx.reports.daily_report(date(2026, 5, 15))
        self.assertEqual(r.totals.total_in, Money(500_000))
        self.assertEqual(r.totals.total_out, Money(300_000))
        self.assertEqual(r.totals.net, Money(200_000))

    def test_public_usage_lines_have_descriptions(self) -> None:
        r = self.ctx.reports.total_report()
        self.assertEqual(len(r.expense_lines), 1)
        self.assertEqual(r.expense_lines[0].description, "Aid")
        self.assertEqual(r.expense_lines[0].amount, Money(300_000))

    def test_public_actor_may_view(self) -> None:
        # None actor (unregistered) holds report.view by default.
        r = self.ctx.reports.total_report(actor=None)
        self.assertEqual(r.totals.net, Money(1_400_000))


class TimezoneBucketingTests(unittest.TestCase):
    def test_late_utc_donation_falls_in_next_local_day(self) -> None:
        ctx = app.build(now=datetime(2026, 5, 16, 12, 0, tzinfo=UTC))
        # 2026-05-15 20:00 UTC == 2026-05-16 01:00 in Tashkent.
        app.seed_donation(ctx, 100_000, datetime(2026, 5, 15, 20, 0, tzinfo=UTC))
        self.assertEqual(ctx.reports.daily_report(date(2026, 5, 15)).totals.total_in, Money(0))
        self.assertEqual(ctx.reports.daily_report(date(2026, 5, 16)).totals.total_in, Money(100_000))


class StatisticsTests(unittest.TestCase):
    def test_statistics_snapshot(self) -> None:
        ctx = app.build(now=datetime(2026, 5, 15, 12, 0, tzinfo=UTC))
        app.seed_donation(ctx, 500_000, datetime(2026, 5, 15, 12, 0, tzinfo=UTC))  # today
        app.seed_donation(ctx, 100_000, datetime(2026, 5, 2, 8, 0, tzinfo=UTC))  # this month
        app.seed_donation(ctx, 50_000, datetime(2026, 1, 10, 8, 0, tzinfo=UTC))  # this year
        stats = ctx.reports.statistics()
        self.assertEqual(stats.today.total_in, Money(500_000))
        self.assertEqual(stats.this_month.total_in, Money(600_000))
        self.assertEqual(stats.this_year.total_in, Money(650_000))
        self.assertEqual(stats.all_time.total_in, Money(650_000))
        self.assertEqual(stats.generated_at, datetime(2026, 5, 15, 12, 0, tzinfo=UTC))


if __name__ == "__main__":
    unittest.main()
