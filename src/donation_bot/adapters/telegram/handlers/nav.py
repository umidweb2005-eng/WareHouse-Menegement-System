"""Navigation handlers: cancel and back.

Registered before feature routers so that pressing Cancel/Back always works,
including in the middle of an FSM flow (clears state and returns to the menu).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from donation_bot.adapters.telegram import labels
from donation_bot.adapters.telegram.keyboards import main_menu
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="nav")


@router.message(F.text == labels.CANCEL)
async def on_cancel(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await state.clear()
    await message.answer(tr.t("common.cancelled"), reply_markup=main_menu(actor, tr))


@router.message(F.text == labels.BACK)
async def on_back(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await state.clear()
    await message.answer(tr.t("menu.title"), reply_markup=main_menu(actor, tr))
