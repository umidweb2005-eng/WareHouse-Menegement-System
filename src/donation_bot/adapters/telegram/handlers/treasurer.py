"""Treasurer flows: record donation, record usage/expense, view recent entries.

Each flow is a guided FSM with per-step Back navigation and a confirmation screen
before the use case runs. Cancel (global) aborts to the main menu; Back steps to
the previous screen (or the main menu from the first step). Handlers stay thin —
validation and persistence happen in the tested use cases.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from donation_bot.adapters.telegram import labels
from donation_bot.adapters.telegram.formatting import (
    format_donation_confirmation,
    format_expense_confirmation,
    format_recent_entries,
)
from donation_bot.adapters.telegram.keyboards import (
    category_menu,
    confirm_menu,
    form_menu,
    main_menu,
    note_menu,
    source_menu,
)
from donation_bot.adapters.telegram.parsing import AmountParseError, parse_amount_to_money
from donation_bot.adapters.telegram.states import DonationFSM, ExpenseFSM
from donation_bot.adapters.telegram.support import EXPENSE_CATEGORIES
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import ApplicationError, PermissionDeniedError
from donation_bot.application.expenses.record_expense import RecordExpenseCommand
from donation_bot.composition.container import Container
from donation_bot.domain.access.entities import StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.errors import DomainError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="treasurer")


def _can(actor: StaffUser | None, permission: Permission) -> bool:
    return actor is not None and actor.has_permission(permission)


async def _to_menu(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await state.clear()
    await message.answer(tr.t("menu.title"), reply_markup=main_menu(actor, tr))


# --------------------------------------------------------------------------- #
# Record donation
# --------------------------------------------------------------------------- #
async def _d_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(DonationFSM.amount)
    await message.answer(tr.t("donation.ask_amount"), reply_markup=form_menu(tr))


async def _d_source(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(DonationFSM.source)
    await message.answer(tr.t("donation.ask_source"), reply_markup=source_menu(tr))


async def _d_note(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(DonationFSM.note)
    await message.answer(tr.t("donation.ask_note"), reply_markup=note_menu(tr))


async def _d_confirm(message: Message, state: FSMContext, tr: Translator) -> None:
    data = await state.get_data()
    text = format_donation_confirmation(
        Money(int(data["amount_minor"])), DonationSource(data["source"]), data.get("note"), tr
    )
    await state.set_state(DonationFSM.confirm)
    await message.answer(text, reply_markup=confirm_menu(tr))


@router.message(StateFilter(None), F.text == labels.RECORD_DONATION)
async def donation_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.DONATION_RECORD):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await _d_amount(message, state, tr)


@router.message(DonationFSM.amount, F.text == labels.BACK)
async def donation_amount_back(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await _to_menu(message, state, actor, tr)


@router.message(DonationFSM.amount)
async def donation_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"), reply_markup=form_menu(tr))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await _d_source(message, state, tr)


@router.message(DonationFSM.source, F.text == labels.BACK)
async def donation_source_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _d_amount(message, state, tr)


@router.message(DonationFSM.source, F.text.in_({labels.SRC_CASH, labels.SRC_BANK}))
async def donation_source(message: Message, state: FSMContext, tr: Translator) -> None:
    source = DonationSource.CASH if message.text == labels.SRC_CASH else DonationSource.BANK_MANUAL
    await state.update_data(source=source.value)
    await _d_note(message, state, tr)


@router.message(DonationFSM.source)
async def donation_source_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("donation.ask_source"), reply_markup=source_menu(tr))


@router.message(DonationFSM.note, F.text == labels.BACK)
async def donation_note_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _d_source(message, state, tr)


@router.message(DonationFSM.note, F.text == labels.SKIP)
async def donation_note_skip(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(note=None)
    await _d_confirm(message, state, tr)


@router.message(DonationFSM.note)
async def donation_note_text(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(note=message.text)
    await _d_confirm(message, state, tr)


@router.message(DonationFSM.confirm, F.text == labels.BACK)
async def donation_confirm_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _d_note(message, state, tr)


@router.message(DonationFSM.confirm, F.text == labels.CONFIRM)
async def donation_confirm(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    data = await state.get_data()
    await state.clear()
    command = RecordDonationCommand(
        actor=actor,  # type: ignore[arg-type]  # guarded at flow start
        amount=Money(int(data["amount_minor"])),
        source=DonationSource(data["source"]),
        event_at=container.clock.now(),
        note=data.get("note"),
    )
    try:
        result = container.record_donation.execute(command)
    except PermissionDeniedError:
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    except (ApplicationError, DomainError):
        await message.answer(tr.t("error.generic"), reply_markup=main_menu(actor, tr))
        return
    await message.answer(
        tr.t("donation.recorded", ref=result.reference_no), reply_markup=main_menu(actor, tr)
    )


@router.message(DonationFSM.confirm)
async def donation_confirm_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("donation.confirm_title"), reply_markup=confirm_menu(tr))


# --------------------------------------------------------------------------- #
# Record usage / expense
# --------------------------------------------------------------------------- #
async def _e_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(ExpenseFSM.amount)
    await message.answer(tr.t("expense.ask_amount"), reply_markup=form_menu(tr))


async def _e_category(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(ExpenseFSM.category)
    await message.answer(tr.t("expense.ask_category"), reply_markup=category_menu(tr))


async def _e_description(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.set_state(ExpenseFSM.description)
    await message.answer(tr.t("expense.ask_description"), reply_markup=form_menu(tr))


async def _e_confirm(message: Message, state: FSMContext, tr: Translator) -> None:
    data = await state.get_data()
    category_name = EXPENSE_CATEGORIES.get(int(data["category_id"]), "")
    text = format_expense_confirmation(
        Money(int(data["amount_minor"])), category_name, data["description"], tr
    )
    await state.set_state(ExpenseFSM.confirm)
    await message.answer(text, reply_markup=confirm_menu(tr))


@router.message(StateFilter(None), F.text == labels.RECORD_EXPENSE)
async def expense_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.EXPENSE_RECORD):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await _e_amount(message, state, tr)


@router.message(ExpenseFSM.amount, F.text == labels.BACK)
async def expense_amount_back(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await _to_menu(message, state, actor, tr)


@router.message(ExpenseFSM.amount)
async def expense_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"), reply_markup=form_menu(tr))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await _e_category(message, state, tr)


@router.message(ExpenseFSM.category, F.text == labels.BACK)
async def expense_category_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _e_amount(message, state, tr)


@router.message(ExpenseFSM.category)
async def expense_category(message: Message, state: FSMContext, tr: Translator) -> None:
    category_id = labels.CATEGORY_ID_BY_LABEL.get(message.text or "")
    if category_id is None:
        await message.answer(tr.t("expense.ask_category"), reply_markup=category_menu(tr))
        return
    await state.update_data(category_id=category_id)
    await _e_description(message, state, tr)


@router.message(ExpenseFSM.description, F.text == labels.BACK)
async def expense_description_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _e_category(message, state, tr)


@router.message(ExpenseFSM.description)
async def expense_description(message: Message, state: FSMContext, tr: Translator) -> None:
    description = (message.text or "").strip()
    if not description:
        await message.answer(tr.t("error.empty_text"), reply_markup=form_menu(tr))
        return
    await state.update_data(description=description)
    await _e_confirm(message, state, tr)


@router.message(ExpenseFSM.confirm, F.text == labels.BACK)
async def expense_confirm_back(message: Message, state: FSMContext, tr: Translator) -> None:
    await _e_description(message, state, tr)


@router.message(ExpenseFSM.confirm, F.text == labels.CONFIRM)
async def expense_confirm(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    data = await state.get_data()
    await state.clear()
    command = RecordExpenseCommand(
        actor=actor,  # type: ignore[arg-type]
        amount=Money(int(data["amount_minor"])),
        category_id=int(data["category_id"]),
        description=data["description"],
        event_at=container.clock.now(),
    )
    try:
        result = container.record_expense.execute(command)
    except PermissionDeniedError:
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    except (ApplicationError, DomainError):
        await message.answer(tr.t("error.generic"), reply_markup=main_menu(actor, tr))
        return
    text = tr.t("expense.recorded", ref=result.reference_no)
    if result.overspent:
        text += "\n" + tr.t("expense.overspent_warning")
    await message.answer(text, reply_markup=main_menu(actor, tr))


@router.message(ExpenseFSM.confirm)
async def expense_confirm_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("expense.confirm_title"), reply_markup=confirm_menu(tr))


# --------------------------------------------------------------------------- #
# Recent entries (staff-only read)
# --------------------------------------------------------------------------- #
@router.message(StateFilter(None), F.text == labels.RECENT_ENTRIES)
async def recent_entries(message: Message, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.ENTRY_ANNOTATE):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    entries = container.list_recent_entries.execute(actor)
    text = format_recent_entries(entries, tr, container.settings.app.org_timezone)
    await message.answer(text, reply_markup=main_menu(actor, tr))
