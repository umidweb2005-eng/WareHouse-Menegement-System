"""Tests for the environment configuration loader.

Written with the standard library ``unittest`` so it runs even where pytest and
third-party packages are unavailable (``python tests/unit/test_config.py``);
pytest also collects it normally.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from donation_bot.infrastructure.config import (
    AppEnv,
    BotMode,
    ConfigError,
    load_dotenv,
    load_settings,
    parse_dotenv,
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


class ParseDotenvTests(unittest.TestCase):
    def test_basic_and_export_and_comments(self) -> None:
        env = parse_dotenv("A=1\nB = two\n# a comment\n\nexport C=three\n")
        self.assertEqual(env, {"A": "1", "B": "two", "C": "three"})

    def test_quotes_preserve_spaces_and_hash(self) -> None:
        env = parse_dotenv('X="a # b"\nY=\'  spaced  \'\n')
        self.assertEqual(env["X"], "a # b")
        self.assertEqual(env["Y"], "  spaced  ")

    def test_inline_comment_stripped_but_not_inside_values(self) -> None:
        env = parse_dotenv("K=value   # trailing\nCRON=0 2 * * *\n")
        self.assertEqual(env["K"], "value")
        self.assertEqual(env["CRON"], "0 2 * * *")

    def test_invalid_lines_are_skipped(self) -> None:
        self.assertEqual(parse_dotenv("noequals\n123=bad\n=nokey\n"), {})


class LoadDotenvTests(unittest.TestCase):
    def test_existing_env_vars_win_and_missing_are_filled(self) -> None:
        os.environ.pop("DOTENV_TEST_NEW", None)
        os.environ["DOTENV_TEST_KEEP"] = "real"
        try:
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / ".env"
                path.write_text("DOTENV_TEST_NEW=fromfile\nDOTENV_TEST_KEEP=fromfile\n")
                self.assertTrue(load_dotenv(path))
            self.assertEqual(os.environ["DOTENV_TEST_NEW"], "fromfile")  # filled in
            self.assertEqual(os.environ["DOTENV_TEST_KEEP"], "real")  # not overridden
        finally:
            os.environ.pop("DOTENV_TEST_NEW", None)
            os.environ.pop("DOTENV_TEST_KEEP", None)

    def test_missing_file_is_noop(self) -> None:
        self.assertFalse(load_dotenv("/no/such/place/.env"))


class LoadSettingsFromDotenvTests(unittest.TestCase):
    """End-to-end: a valid .env in the working directory makes load_settings() work
    without exporting any variables (the reported bug)."""

    def _clean_environ(self):
        keys = list(BASE_ENV) + ["FIRST_SUPER_ADMIN_NAME"]
        saved = {k: os.environ.pop(k, None) for k in keys}
        return keys, saved

    def _restore_environ(self, keys, saved):
        for k in keys:
            os.environ.pop(k, None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

    def test_loads_from_env_file_in_cwd(self) -> None:
        keys, saved = self._clean_environ()
        cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / ".env").write_text(
                    "\n".join(f"{k}={v}" for k, v in BASE_ENV.items()) + "\n"
                )
                os.chdir(d)
                settings = load_settings()  # env=None -> should read .env
                self.assertEqual(settings.telegram.bot_token, "123:abc")
                self.assertEqual(settings.bootstrap.first_super_admin_telegram_id, 987654321)
        finally:
            os.chdir(cwd)
            self._restore_environ(keys, saved)

    def test_real_env_var_overrides_env_file(self) -> None:
        keys, saved = self._clean_environ()
        cwd = os.getcwd()
        try:
            os.environ["APP_ENV"] = "production"  # override the file value below
            with tempfile.TemporaryDirectory() as d:
                lines = [f"{k}={v}" for k, v in BASE_ENV.items() if k != "APP_ENV"]
                lines.append("APP_ENV=development")
                (Path(d) / ".env").write_text("\n".join(lines) + "\n")
                os.chdir(d)
                settings = load_settings()
                self.assertEqual(settings.app.env, AppEnv.PRODUCTION)  # env wins over .env
        finally:
            os.chdir(cwd)
            self._restore_environ(keys, saved)


if __name__ == "__main__":
    unittest.main()
