"""Application entrypoint.

Loads and validates configuration, sets up logging, then runs the Telegram bot
(in-memory backend for now). The persistence backend is swapped in the composition
root later without touching handlers or use cases.
"""

from __future__ import annotations

import asyncio

from donation_bot import __version__
from donation_bot.infrastructure.config import ConfigError, load_settings
from donation_bot.infrastructure.logging import configure_logging, get_logger


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as exc:
        # Fail fast with a clear message; do not start with partial config.
        print(str(exc))
        return 2

    configure_logging(settings.app.log_level)
    log = get_logger("donation_bot")
    log.info(
        "donation-bot %s starting (env=%s, mode=%s)",
        __version__,
        settings.app.env.value,
        settings.telegram.mode.value,
    )

    # Imported lazily so configuration/tests do not require aiogram to be installed.
    from donation_bot.adapters.telegram.app import run

    asyncio.run(run(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
