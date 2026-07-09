"""Fallback handler: any unrecognized message *outside* a flow re-shows the menu.

Registered last so specific handlers win. ``StateFilter(None)`` ensures it does not
interfere with active FSM flows (which handle their own unexpected input).
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from donation_bot.adapters.telegram.keyboards import main_menu
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="fallback")


@router.message(StateFilter(None))
async def on_unknown(message: Message, actor: StaffUser | None, tr: Translator) -> None:
    await message.answer(tr.t("common.unknown"), reply_markup=main_menu(actor, tr))
