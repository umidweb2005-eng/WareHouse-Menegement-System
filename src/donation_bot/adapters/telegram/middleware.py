"""Actor-resolution middleware.

Runs on every update, resolves the caller's Telegram ID to a staff actor (or
``None`` for public/donor users, who are never persisted), and injects the actor,
translator, and container into handler data. Business permission checks still
happen inside the use cases.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from donation_bot.application.access.identity import resolve_actor
from donation_bot.composition.container import Container


class ActorMiddleware(BaseMiddleware):
    def __init__(self, container: Container) -> None:
        self._container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        actor = None
        if user is not None:
            # Public users' Telegram IDs are used transiently here and never stored.
            actor = resolve_actor(self._container.staff_repo, user.id)
        data["actor"] = actor
        data["tr"] = self._container.translator
        data["container"] = self._container
        return await handler(event, data)
