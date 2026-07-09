"""Logging setup.

Privacy rule (see ``docs/SECURITY.md`` §9): logs must never contain donor
identifiers or private free text (annotation / reversal-reason content). For
public-user interactions the Telegram ID is not logged at all. This module only
configures formatting/levels; call sites are responsible for not passing PII.
"""

from __future__ import annotations

import logging

_CONFIGURED = False

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format=_LOG_FORMAT)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger. Use ``get_logger(__name__)`` at call sites."""
    return logging.getLogger(name)
