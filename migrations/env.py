"""Alembic environment.

Scaffold for M0. The target metadata (SQLAlchemy models) and the append-only
triggers / least-privilege grants are added in the persistence milestone (M2);
see docs/DATABASE_DESIGN.md. The migration database URL is derived from the
application settings using the privileged migration role — never the app role.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from donation_bot.infrastructure.config import load_settings

config = context.config

# Supply the migration-role DSN from validated settings (not hard-coded in .ini).
_settings = load_settings()
config.set_main_option("sqlalchemy.url", _settings.database.migration_dsn())

# Set to the models' MetaData in M2 (e.g., ``from donation_bot.adapters.persistence
# import metadata as target_metadata``). ``None`` for the initial scaffold.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
