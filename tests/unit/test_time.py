"""Reporting-period tests (invariant I8: org-timezone bucketing, UTC storage)."""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from donation_bot.domain.time import (
    custom_period,
    day_period,
    month_period,
    year_period,
)

TASHKENT = "Asia/Tashkent"  # UTC+05:00, no DST


class DayPeriodTests(unittest.TestCase):
    def test_day_maps_to_utc_offset(self) -> None:
        # 2026-01-01 in Tashkent starts at 2025-12-31 19:00 UTC (+05:00).
        p = day_period(date(2026, 1, 1), TASHKENT)
        self.assertEqual(p.start, datetime(2025, 12, 31, 19, 0, tzinfo=timezone.utc))
        self.assertEqual(p.end, datetime(2026, 1, 1, 19, 0, tzinfo=timezone.utc))

    def test_late_utc_event_belongs_to_next_local_day(self) -> None:
        # 20:00 UTC on Jan 1 is 01:00 local on Jan 2 -> belongs to Jan 2, not Jan 1.
        moment = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
        self.assertFalse(day_period(date(2026, 1, 1), TASHKENT).contains(moment))
        self.assertTrue(day_period(date(2026, 1, 2), TASHKENT).contains(moment))

    def test_adjacent_days_are_half_open_and_contiguous(self) -> None:
        d1 = day_period(date(2026, 3, 10), TASHKENT)
        d2 = day_period(date(2026, 3, 11), TASHKENT)
        self.assertEqual(d1.end, d2.start)  # no gap, no overlap


class MonthYearPeriodTests(unittest.TestCase):
    def test_december_rolls_into_next_year(self) -> None:
        p = month_period(2026, 12, TASHKENT)
        self.assertEqual(p.start, datetime(2026, 11, 30, 19, 0, tzinfo=timezone.utc))
        self.assertEqual(p.end, datetime(2026, 12, 31, 19, 0, tzinfo=timezone.utc))

    def test_year_period_spans_twelve_months(self) -> None:
        p = year_period(2026, TASHKENT)
        self.assertEqual(p.start, datetime(2025, 12, 31, 19, 0, tzinfo=timezone.utc))
        self.assertEqual(p.end, datetime(2026, 12, 31, 19, 0, tzinfo=timezone.utc))


class CustomPeriodTests(unittest.TestCase):
    def test_inclusive_end_day(self) -> None:
        p = custom_period(date(2026, 1, 1), date(2026, 1, 31), TASHKENT)
        # end is exclusive midnight of Feb 1 local == Jan 31 19:00 UTC
        self.assertEqual(p.end, datetime(2026, 1, 31, 19, 0, tzinfo=timezone.utc))

    def test_end_before_start_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            custom_period(date(2026, 2, 1), date(2026, 1, 1), TASHKENT)


if __name__ == "__main__":
    unittest.main()
