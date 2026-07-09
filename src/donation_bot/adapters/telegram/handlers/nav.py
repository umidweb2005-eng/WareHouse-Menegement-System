"""Global navigation: Cancel (any state) and Back (only outside a flow).

Cancel always aborts the current flow and restores the main menu. Back *inside* an
FSM steps back one screen and is handled by each flow router; here Back only
applies when there is no active flow (``StateFilter(None)``), returning to the
main menu (e.g., from the reports sub-menu). This router is included first so
Cancel wins over any in-flow input handler.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
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


@router.message(StateFilter(None), F.text == labels.BACK)
async def on_back_to_menu(message: Message, actor: StaffUser | None, tr: Translator) -> None:
    await message.answer(tr.t("menu.title"), reply_markup=main_menu(actor, tr))
