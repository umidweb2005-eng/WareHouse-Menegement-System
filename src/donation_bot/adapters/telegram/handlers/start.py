"""/start handler: greet and render the role-appropriate main menu."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from donation_bot.adapters.telegram.keyboards import main_menu
from donation_bot.adapters.telegram.support import role_label
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, actor: StaffUser | None, tr: Translator) -> None:
    if actor is None:
        await message.answer(tr.t("start.greeting.public"))
    else:
        await message.answer(
            tr.t("start.greeting.staff", name=actor.display_name or "", role=role_label(actor, tr))
        )
    await message.answer(tr.t("menu.hint"), reply_markup=main_menu(actor, tr))
