"""Tests for the environment configuration loader.

Written with the standard library ``unittest`` so it runs even where pytest and
third-party packages are unavailable (``python tests/unit/test_config.py``);
pytest also collects it normally.
"""

from __future__ import annotations

import unittest

from donation_bot.infrastructure.config import (
    AppEnv,
    BotMode,
    ConfigError,
    load_settings,
)

BASE_ENV = {
    "APP_ENV": "production",
    "BOT_TOKEN": "123:abc",
    "BOT_MODE": "polling",
    "POSTGRES_HOST": "db",
    "POSTGRES_DB": "donation_bot",
    "APP_DB_USER": "donation_app",
    "APP_DB_PASSWORD": "app_secret",
    "MIGRATION_DB_USER": "donation_migrator",
    "MIGRATION_DB_PASSWORD": "mig_secret",
    "FIRST_SUPER_ADMIN_TELEGRAM_ID": "987654321",
}


class LoadSettingsValidTests(unittest.TestCase):
    def test_loads_a_valid_environment(self) -> None:
        settings = load_settings(BASE_ENV)
        self.assertEqual(settings.app.env, AppEnv.PRODUCTION)
        self.assertEqual(settings.telegram.mode, BotMode.POLLING)
        self.assertEqual(settings.telegram.bot_token, "123:abc")
        self.assertEqual(settings.database.port, 5432)  # default
        self.assertEqual(settings.bootstrap.first_super_admin_telegram_id, 987654321)

    def test_defaults_are_applied(self) -> None:
        settings = load_settings(BASE_ENV)
        self.assertEqual(settings.app.default_locale, "uz")
        self.assertEqual(settings.app.org_timezone, "Asia/Tashkent")
        self.assertEqual(settings.backup.retention_days, 30)

    def test_dsn_uses_correct_roles_and_never_crosses_them(self) -> None:
        db = load_settings(BASE_ENV).database
        self.assertIn("donation_app:app_secret@db:5432/donation_bot", db.app_dsn())
        self.assertIn("donation_migrator:mig_secret@db:5432/donation_bot", db.migration_dsn())
        self.assertTrue(db.app_dsn().startswith("postgresql+asyncpg://"))


class LoadSettingsInvalidTests(unittest.TestCase):
    def test_missing_required_fields_are_reported_together(self) -> None:
        with self.assertRaises(ConfigError) as ctx:
            load_settings({"BOT_MODE": "polling"})
        # Aggregates all problems in one pass (fail-fast, operator-friendly).
        self.assertGreaterEqual(len(ctx.exception.errors), 5)
        self.assertTrue(any("BOT_TOKEN" in e for e in ctx.exception.errors))

    def test_webhook_mode_requires_webhook_fields(self) -> None:
        env = {**BASE_ENV, "BOT_MODE": "webhook"}
        with self.assertRaises(ConfigError) as ctx:
            load_settings(env)
        joined = " ".join(ctx.exception.errors)
        self.assertIn("WEBHOOK_BASE_URL", joined)
        self.assertIn("WEBHOOK_SECRET", joined)

    def test_non_integer_admin_id_is_rejected(self) -> None:
        env = {**BASE_ENV, "FIRST_SUPER_ADMIN_TELEGRAM_ID": "not-a-number"}
        with self.assertRaises(ConfigError) as ctx:
            load_settings(env)
        self.assertTrue(
            any("FIRST_SUPER_ADMIN_TELEGRAM_ID" in e for e in ctx.exception.errors)
        )

    def test_invalid_enum_value_is_rejected(self) -> None:
        env = {**BASE_ENV, "BOT_MODE": "carrier-pigeon"}
        with self.assertRaises(ConfigError) as ctx:
            load_settings(env)
        self.assertTrue(any("BOT_MODE" in e for e in ctx.exception.errors))


if __name__ == "__main__":
    unittest.main()
