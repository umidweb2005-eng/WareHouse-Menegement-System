"""Typed, fail-fast application configuration loaded from the environment.

This is the single place that reads environment variables. Everything else in the
codebase receives a typed :class:`Settings` object. Loading is intentionally
dependency-free (standard library only) so it is testable without installing any
third-party package, and it fails fast with a clear, aggregated error listing
*all* problems at once rather than surfacing them one at a time.

See ``docs/CONFIGURATION.md`` for the authoritative list of variables.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

# Public re-exports
__all__ = [
    "AppEnv",
    "BotMode",
    "ConfigError",
    "AppConfig",
    "TelegramConfig",
    "DatabaseConfig",
    "BootstrapConfig",
    "BackupConfig",
    "Settings",
    "load_settings",
]


class ConfigError(Exception):
    """Raised when configuration is missing or invalid.

    The message aggregates every problem found so an operator can fix them in one
    pass rather than rerunning repeatedly.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        joined = "\n  - ".join(errors)
        super().__init__(f"Invalid configuration:\n  - {joined}")


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class BotMode(str, Enum):
    WEBHOOK = "webhook"
    POLLING = "polling"


@dataclass(frozen=True, slots=True)
class AppConfig:
    env: AppEnv
    log_level: str
    default_locale: str
    org_timezone: str


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    bot_token: str
    mode: BotMode
    webhook_base_url: str | None
    webhook_secret: str | None
    webhook_port: int


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    app_user: str
    app_password: str
    migration_user: str
    migration_password: str

    def dsn(self, *, user: str, password: str, driver: str = "postgresql+asyncpg") -> str:
        """Build a SQLAlchemy DSN for the given credentials (never logged)."""
        return f"{driver}://{user}:{password}@{self.host}:{self.port}/{self.name}"

    def app_dsn(self, driver: str = "postgresql+asyncpg") -> str:
        return self.dsn(user=self.app_user, password=self.app_password, driver=driver)

    def migration_dsn(self, driver: str = "postgresql+psycopg2") -> str:
        return self.dsn(
            user=self.migration_user, password=self.migration_password, driver=driver
        )


@dataclass(frozen=True, slots=True)
class BootstrapConfig:
    first_super_admin_telegram_id: int
    first_super_admin_name: str | None


@dataclass(frozen=True, slots=True)
class BackupConfig:
    dir: str
    schedule_cron: str
    retention_days: int
    encryption_key: str | None
    offsite_target: str | None


@dataclass(frozen=True, slots=True)
class Settings:
    app: AppConfig
    telegram: TelegramConfig
    database: DatabaseConfig
    bootstrap: BootstrapConfig
    backup: BackupConfig


class _Loader:
    """Collects errors while reading a mapping, so all issues surface together."""

    def __init__(self, env: Mapping[str, str]) -> None:
        self._env = env
        self.errors: list[str] = []

    def required(self, key: str) -> str:
        value = self._env.get(key, "").strip()
        if not value:
            self.errors.append(f"{key} is required")
            return ""
        return value

    def optional(self, key: str, default: str | None = None) -> str | None:
        value = self._env.get(key)
        if value is None:
            return default
        value = value.strip()
        return value or default

    def required_int(self, key: str) -> int:
        raw = self._env.get(key, "").strip()
        if not raw:
            self.errors.append(f"{key} is required")
            return 0
        try:
            return int(raw)
        except ValueError:
            self.errors.append(f"{key} must be an integer (got {raw!r})")
            return 0

    def optional_int(self, key: str, default: int) -> int:
        raw = self._env.get(key)
        if raw is None or not raw.strip():
            return default
        try:
            return int(raw.strip())
        except ValueError:
            self.errors.append(f"{key} must be an integer (got {raw!r})")
            return default

    def enum(self, key: str, enum_cls: type[Enum], default: Enum | None = None) -> Enum:
        raw = self._env.get(key)
        if raw is None or not raw.strip():
            if default is not None:
                return default
            self.errors.append(f"{key} is required")
            return next(iter(enum_cls))
        try:
            return enum_cls(raw.strip().lower())
        except ValueError:
            allowed = ", ".join(e.value for e in enum_cls)
            self.errors.append(f"{key} must be one of [{allowed}] (got {raw!r})")
            return default if default is not None else next(iter(enum_cls))


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load and validate settings from ``env`` (defaults to ``os.environ``).

    Raises :class:`ConfigError` listing every problem if anything is missing or
    invalid.
    """
    loader = _Loader(os.environ if env is None else env)

    app = AppConfig(
        env=AppEnv(loader.enum("APP_ENV", AppEnv, AppEnv.PRODUCTION)),
        log_level=(loader.optional("LOG_LEVEL", "INFO") or "INFO").upper(),
        default_locale=loader.optional("DEFAULT_LOCALE", "uz") or "uz",
        org_timezone=loader.optional("ORG_TIMEZONE", "Asia/Tashkent") or "Asia/Tashkent",
    )

    mode = BotMode(loader.enum("BOT_MODE", BotMode, BotMode.POLLING))
    webhook_base_url = loader.optional("WEBHOOK_BASE_URL")
    webhook_secret = loader.optional("WEBHOOK_SECRET")
    if mode is BotMode.WEBHOOK:
        if not webhook_base_url:
            loader.errors.append("WEBHOOK_BASE_URL is required when BOT_MODE=webhook")
        if not webhook_secret:
            loader.errors.append("WEBHOOK_SECRET is required when BOT_MODE=webhook")
    telegram = TelegramConfig(
        bot_token=loader.required("BOT_TOKEN"),
        mode=mode,
        webhook_base_url=webhook_base_url,
        webhook_secret=webhook_secret,
        webhook_port=loader.optional_int("WEBHOOK_PORT", 8080),
    )

    database = DatabaseConfig(
        host=loader.required("POSTGRES_HOST"),
        port=loader.optional_int("POSTGRES_PORT", 5432),
        name=loader.required("POSTGRES_DB"),
        app_user=loader.required("APP_DB_USER"),
        app_password=loader.required("APP_DB_PASSWORD"),
        migration_user=loader.required("MIGRATION_DB_USER"),
        migration_password=loader.required("MIGRATION_DB_PASSWORD"),
    )

    bootstrap = BootstrapConfig(
        first_super_admin_telegram_id=loader.required_int("FIRST_SUPER_ADMIN_TELEGRAM_ID"),
        first_super_admin_name=loader.optional("FIRST_SUPER_ADMIN_NAME"),
    )

    backup = BackupConfig(
        dir=loader.optional("BACKUP_DIR", "/data/backups") or "/data/backups",
        schedule_cron=loader.optional("BACKUP_SCHEDULE_CRON", "0 2 * * *") or "0 2 * * *",
        retention_days=loader.optional_int("BACKUP_RETENTION_DAYS", 30),
        encryption_key=loader.optional("BACKUP_ENCRYPTION_KEY"),
        offsite_target=loader.optional("BACKUP_OFFSITE_TARGET"),
    )

    if loader.errors:
        raise ConfigError(loader.errors)

    return Settings(
        app=app,
        telegram=telegram,
        database=database,
        bootstrap=bootstrap,
        backup=backup,
    )
