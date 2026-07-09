"""Anonymous donation management Telegram bot.

Telegram-first system for recording donations and expenses with two binding
principles: donor privacy is absolute, and every reported figure is derived from
an immutable ledger (transparency). See ``docs/`` for the authoritative design.

Package layout (hexagonal / ports & adapters):

- ``domain``         Pure business core (no framework, no I/O).
- ``application``    Use cases + ports (interfaces the core needs).
- ``adapters``       Concrete implementations: Telegram, persistence, scheduler.
- ``infrastructure`` Config, DB engine, logging, i18n.
- ``composition``    Dependency-injection wiring (composition root).
"""

__version__ = "0.1.0"
