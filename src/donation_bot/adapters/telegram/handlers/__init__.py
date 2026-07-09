"""Handler routers aggregated into a single router for the dispatcher.

Order matters: navigation (cancel/back) first so it always wins; then the /start
command; then the feature routers; and the catch-all fallback last.
"""

from __future__ import annotations

from aiogram import Router

from donation_bot.adapters.telegram.handlers import (
    admin,
    fallback,
    nav,
    public,
    start,
    treasurer,
)


def build_router() -> Router:
    router = Router(name="handlers")
    router.include_router(nav.router)
    router.include_router(start.router)
    router.include_router(public.router)
    router.include_router(treasurer.router)
    router.include_router(admin.router)
    router.include_router(fallback.router)
    return router


router = build_router()
