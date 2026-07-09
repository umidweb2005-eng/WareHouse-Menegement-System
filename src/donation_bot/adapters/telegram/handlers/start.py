"""/start: greet and show the role-appropriate main menu in a single message."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from donation_bot.adapters.telegram.keyboards import main_menu
from donation_bot.adapters.telegram.support import role_label
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await state.clear()  # /start always resets any in-progress flow
    if actor is None:
        text = tr.t("start.greeting.public")
    else:
        text = tr.t("start.greeting.staff", name=actor.display_name or "", role=role_label(actor, tr))
    await message.answer(text, reply_markup=main_menu(actor, tr))
