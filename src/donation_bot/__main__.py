"""Application entrypoint (stub).

Loads configuration and sets up logging. The composition root and Telegram
adapter are wired in later implementation milestones (see ``docs/ROADMAP.md``);
until then this only validates that the environment is configured correctly.
"""

from __future__ import annotations

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
    log.info("donation-bot %s starting (env=%s)", __version__, settings.app.env.value)
    log.info(
        "Bot runtime is not wired yet; this milestone provides the project "
        "skeleton and configuration only. See docs/ROADMAP.md (Phase 3)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
