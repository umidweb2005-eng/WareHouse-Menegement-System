"""Treasurer flows: record a donation, record a usage/expense.

Each flow is a guided FSM ending in a confirmation screen before the use case
runs. Cancellation is handled globally by the nav router. Handlers stay thin —
validation and persistence happen in the (already tested) use cases.
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
)
from donation_bot.adapters.telegram.keyboards import (
    cancel_menu,
    category_menu,
    confirm_menu,
    main_menu,
    skip_cancel_menu,
    source_menu,
)
from donation_bot.adapters.telegram.states import DonationFSM, ExpenseFSM
from donation_bot.adapters.telegram.parsing import AmountParseError, parse_amount_to_money
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


# --------------------------------------------------------------------------- #
# Record donation
# --------------------------------------------------------------------------- #
@router.message(StateFilter(None), F.text == labels.RECORD_DONATION)
async def donation_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.DONATION_RECORD):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await state.set_state(DonationFSM.amount)
    await message.answer(tr.t("donation.ask_amount"), reply_markup=cancel_menu(tr))


@router.message(DonationFSM.amount)
async def donation_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await state.set_state(DonationFSM.source)
    await message.answer(tr.t("donation.ask_source"), reply_markup=source_menu(tr))


@router.message(DonationFSM.source, F.text.in_({labels.SRC_CASH, labels.SRC_BANK}))
async def donation_source(message: Message, state: FSMContext, tr: Translator) -> None:
    source = DonationSource.CASH if message.text == labels.SRC_CASH else DonationSource.BANK_MANUAL
    await state.update_data(source=source.value)
    await state.set_state(DonationFSM.note)
    await message.answer(tr.t("donation.ask_note"), reply_markup=skip_cancel_menu(tr))


@router.message(DonationFSM.source)
async def donation_source_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("donation.ask_source"), reply_markup=source_menu(tr))


async def _donation_to_confirm(message: Message, state: FSMContext, tr: Translator, note: str | None) -> None:
    await state.update_data(note=note)
    data = await state.get_data()
    text = format_donation_confirmation(
        Money(int(data["amount_minor"])), DonationSource(data["source"]), note, tr
    )
    await state.set_state(DonationFSM.confirm)
    await message.answer(text, reply_markup=confirm_menu(tr))


@router.message(DonationFSM.note, F.text == labels.SKIP)
async def donation_note_skip(message: Message, state: FSMContext, tr: Translator) -> None:
    await _donation_to_confirm(message, state, tr, note=None)


@router.message(DonationFSM.note)
async def donation_note_text(message: Message, state: FSMContext, tr: Translator) -> None:
    await _donation_to_confirm(message, state, tr, note=message.text)


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
@router.message(StateFilter(None), F.text == labels.RECORD_EXPENSE)
async def expense_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.EXPENSE_RECORD):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await state.set_state(ExpenseFSM.amount)
    await message.answer(tr.t("expense.ask_amount"), reply_markup=cancel_menu(tr))


@router.message(ExpenseFSM.amount)
async def expense_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await state.set_state(ExpenseFSM.category)
    await message.answer(tr.t("expense.ask_category"), reply_markup=category_menu(tr))


@router.message(ExpenseFSM.category)
async def expense_category(message: Message, state: FSMContext, tr: Translator) -> None:
    category_id = labels.CATEGORY_ID_BY_LABEL.get(message.text or "")
    if category_id is None:
        await message.answer(tr.t("expense.ask_category"), reply_markup=category_menu(tr))
        return
    await state.update_data(category_id=category_id)
    await state.set_state(ExpenseFSM.description)
    await message.answer(tr.t("expense.ask_description"), reply_markup=cancel_menu(tr))


@router.message(ExpenseFSM.description)
async def expense_description(message: Message, state: FSMContext, tr: Translator) -> None:
    description = (message.text or "").strip()
    if not description:
        await message.answer(tr.t("error.empty_text"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(description=description)
    data = await state.get_data()
    category_name = EXPENSE_CATEGORIES.get(int(data["category_id"]), "")
    text = format_expense_confirmation(
        Money(int(data["amount_minor"])), category_name, description, tr
    )
    await state.set_state(ExpenseFSM.confirm)
    await message.answer(text, reply_markup=confirm_menu(tr))


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
