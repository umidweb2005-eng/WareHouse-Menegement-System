"""Tests for infrastructure adapters and small Telegram support helpers
(all aiogram-free)."""

from __future__ import annotations

import unittest
from datetime import date

import _appsupport as app

from donation_bot.adapters.telegram.support import local_today, role_label
from donation_bot.infrastructure.clock import SystemClock
from donation_bot.infrastructure.ids import UuidGenerator


class SystemClockTests(unittest.TestCase):
    def test_now_is_timezone_aware(self) -> None:
        self.assertIsNotNone(SystemClock().now().tzinfo)


class UuidGeneratorTests(unittest.TestCase):
    def test_ids_are_unique(self) -> None:
        gen = UuidGenerator()
        self.assertNotEqual(gen.new_id(), gen.new_id())


BASE_ENV = {
    "APP_ENV": "development",
    "BOT_TOKEN": "123:abc",
    "BOT_MODE": "polling",
    "POSTGRES_HOST": "db",
    "POSTGRES_DB": "donation_bot",
    "APP_DB_USER": "a",
    "APP_DB_PASSWORD": "b",
    "MIGRATION_DB_USER": "c",
    "MIGRATION_DB_PASSWORD": "d",
    "FIRST_SUPER_ADMIN_TELEGRAM_ID": "777",
    "FIRST_SUPER_ADMIN_NAME": "Boss",
}


class ContainerWiringTests(unittest.TestCase):
    """Exercises the composition root end-to-end with the in-memory backend
    (no aiogram, no database)."""

    def test_build_seed_and_serve(self) -> None:
        from donation_bot.composition.container import build_container
        from donation_bot.infrastructure.config import load_settings

        container = build_container(load_settings(BASE_ENV))
        container.seed()
        container.seed()  # idempotent

        admin = container.staff_repo.get_by_telegram_id(777)
        self.assertIsNotNone(admin)
        # public read paths work with no data yet
        self.assertIsNone(container.get_active_account.execute(actor=None))
        report = container.reports.total_report(actor=None)
        self.assertEqual(report.totals.donation_count, 0)


class SupportHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_local_today_uses_org_timezone(self) -> None:
        self.assertIsInstance(local_today(self.ctx.clock, "Asia/Tashkent"), date)

    def test_role_label(self) -> None:
        from donation_bot.infrastructure.i18n.translator import get_translator

        tr = get_translator("uz")
        self.assertEqual(role_label(None, tr), "")
        self.assertEqual(role_label(self.ctx.admin, tr), tr.t("staff.role_admin"))
        self.assertEqual(role_label(self.ctx.treasurer, tr), tr.t("staff.role_treasurer"))


if __name__ == "__main__":
    unittest.main()
