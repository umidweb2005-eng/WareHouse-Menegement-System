"""Telegram application runner (aiogram 3.x).

Builds the Bot + Dispatcher, wires the actor middleware and handlers, seeds the
first Super Admin, and starts polling. Webhook mode is a follow-up; polling is the
fastest way to interact with the bot now.

NOTE: requires aiogram (installed in real environments; not in the design sandbox).
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from donation_bot.adapters.telegram.handlers import router
from donation_bot.adapters.telegram.middleware import ActorMiddleware
from donation_bot.composition.container import build_container
from donation_bot.infrastructure.config import BotMode, Settings
from donation_bot.infrastructure.logging import get_logger

_log = get_logger("donation_bot.telegram")


async def run(settings: Settings) -> None:
    container = build_container(settings)
    container.seed()  # idempotent: system actor + first Super Admin

    bot = Bot(token=settings.telegram.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ActorMiddleware(container))
    dp.include_router(router)

    if settings.telegram.mode is BotMode.POLLING:
        _log.info("starting Telegram long polling (in-memory backend)")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    else:
        raise NotImplementedError(
            "Webhook mode is not wired yet in v1 — set BOT_MODE=polling to run the bot."
        )
