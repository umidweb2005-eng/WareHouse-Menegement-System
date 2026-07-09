"""Telegram handlers (aiogram 3.x).

Thin adapter: each handler resolves the actor (via middleware), collects input,
calls a use case, and renders a localized reply. No business logic lives here.
Privileged flows pre-check the permission for UX, but the use cases remain the
authoritative enforcement point.

NOTE: not executed in the design sandbox (aiogram is not installed there); this is
written to the aiogram 3.x API and syntax-checked.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from donation_bot.adapters.telegram.keyboards import (
    account_type_menu,
    category_menu,
    main_menu,
    period_menu,
    role_menu,
    skip_menu,
    source_menu,
)
from donation_bot.adapters.telegram.formatting import (
    format_account,
    format_report,
    format_statistics,
)
from donation_bot.adapters.telegram.support import (
    EXPENSE_CATEGORIES,
    local_today,
    role_label,
)
from donation_bot.adapters.telegram.states import (
    ConfigureAccountFSM,
    DonationFSM,
    ExpenseFSM,
    RegisterStaffFSM,
)
from donation_bot.adapters.telegram.parsing import AmountParseError, parse_amount_to_money
from donation_bot.application.access.register_staff import RegisterStaffCommand
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import ApplicationError, PermissionDeniedError
from donation_bot.application.expenses.record_expense import RecordExpenseCommand
from donation_bot.application.settings.configure_account import ConfigureDonationAccountCommand
from donation_bot.composition.container import Container
from donation_bot.domain.access.entities import SUPER_ADMIN_ROLE, TREASURER_ROLE, StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.accounts.entities import AccountType
from donation_bot.domain.errors import DomainError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import Translator

router = Router()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
async def _send(event: Message | CallbackQuery, text: str, reply_markup=None) -> None:
    if isinstance(event, CallbackQuery):
        if event.message is not None:
            await event.message.answer(text, reply_markup=reply_markup)
        await event.answer()
    else:
        await event.answer(text, reply_markup=reply_markup)


def _can(actor: StaffUser | None, permission: Permission) -> bool:
    return actor is not None and actor.has_permission(permission)


# --------------------------------------------------------------------------- #
# Start & main menu
# --------------------------------------------------------------------------- #
@router.message(CommandStart())
async def cmd_start(message: Message, actor: StaffUser | None, tr: Translator) -> None:
    if actor is None:
        await message.answer(tr.t("start.greeting.public"))
    else:
        await message.answer(
            tr.t("start.greeting.staff", name=actor.display_name or "", role=role_label(actor, tr))
        )
    await message.answer(tr.t("menu.title"), reply_markup=main_menu(actor, tr))


@router.callback_query(F.data == "menu")
async def open_menu(callback: CallbackQuery, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    await state.clear()
    await _send(callback, tr.t("menu.title"), reply_markup=main_menu(actor, tr))


# --------------------------------------------------------------------------- #
# Public: donate, statistics, reports
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:donate")
async def show_donate(callback: CallbackQuery, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    account = container.get_active_account.execute(actor=actor)
    await _send(callback, format_account(account, tr), reply_markup=main_menu(actor, tr))


@router.callback_query(F.data == "sec:statistics")
async def show_statistics(callback: CallbackQuery, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    stats = container.reports.statistics(actor=actor)
    await _send(callback, format_statistics(stats, tr), reply_markup=main_menu(actor, tr))


@router.callback_query(F.data == "sec:reports")
async def choose_report(callback: CallbackQuery, tr: Translator) -> None:
    await _send(callback, tr.t("reports.choose_period"), reply_markup=period_menu(tr))


@router.callback_query(F.data.startswith("rep:"))
async def show_report(callback: CallbackQuery, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    period = callback.data.split(":", 1)[1]
    today = local_today(container.clock, container.settings.app.org_timezone)
    if period == "today":
        report = container.reports.daily_report(today, actor=actor)
    elif period == "month":
        report = container.reports.monthly_report(today.year, today.month, actor=actor)
    elif period == "year":
        report = container.reports.yearly_report(today.year, actor=actor)
    else:
        report = container.reports.total_report(actor=actor)
    await _send(callback, format_report(report, tr), reply_markup=period_menu(tr))


# --------------------------------------------------------------------------- #
# Treasurer: record donation
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:record_donation")
async def start_donation(callback: CallbackQuery, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.DONATION_RECORD):
        await _send(callback, tr.t("error.permission_denied"))
        return
    await state.set_state(DonationFSM.amount)
    await _send(callback, tr.t("donation.ask_amount"))


@router.message(DonationFSM.amount)
async def donation_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await state.set_state(DonationFSM.source)
    await message.answer(tr.t("donation.ask_source"), reply_markup=source_menu(tr))


@router.callback_query(DonationFSM.source, F.data.startswith("src:"))
async def donation_source(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    choice = callback.data.split(":", 1)[1]
    source = DonationSource.CASH if choice == "cash" else DonationSource.BANK_MANUAL
    await state.update_data(source=source.value)
    await state.set_state(DonationFSM.note)
    await _send(callback, tr.t("donation.ask_note"), reply_markup=skip_menu(tr))


async def _finalize_donation(
    event: Message | CallbackQuery, state: FSMContext, container: Container,
    actor: StaffUser | None, tr: Translator, note: str | None,
) -> None:
    data = await state.get_data()
    await state.clear()
    command = RecordDonationCommand(
        actor=actor,  # type: ignore[arg-type]  # guarded by _can at flow start
        amount=Money(int(data["amount_minor"])),
        source=DonationSource(data["source"]),
        event_at=container.clock.now(),
        note=note,
    )
    try:
        result = container.record_donation.execute(command)
    except PermissionDeniedError:
        await _send(event, tr.t("error.permission_denied"))
        return
    except (ApplicationError, DomainError):
        await _send(event, tr.t("error.generic"))
        return
    await _send(event, tr.t("donation.recorded", ref=result.reference_no), reply_markup=main_menu(actor, tr))


@router.message(DonationFSM.note)
async def donation_note_text(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finalize_donation(message, state, container, actor, tr, note=message.text)


@router.callback_query(DonationFSM.note, F.data == "skip")
async def donation_note_skip(callback: CallbackQuery, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finalize_donation(callback, state, container, actor, tr, note=None)


# --------------------------------------------------------------------------- #
# Treasurer: record expense (usage)
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:record_expense")
async def start_expense(callback: CallbackQuery, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.EXPENSE_RECORD):
        await _send(callback, tr.t("error.permission_denied"))
        return
    await state.set_state(ExpenseFSM.amount)
    await _send(callback, tr.t("expense.ask_amount"))


@router.message(ExpenseFSM.amount)
async def expense_amount(message: Message, state: FSMContext, tr: Translator) -> None:
    try:
        money = parse_amount_to_money(message.text or "")
    except AmountParseError:
        await message.answer(tr.t("error.invalid_amount"))
        return
    await state.update_data(amount_minor=money.amount_minor)
    await state.set_state(ExpenseFSM.category)
    await message.answer(tr.t("expense.ask_category"), reply_markup=category_menu(tr))


@router.callback_query(ExpenseFSM.category, F.data.startswith("cat:"))
async def expense_category(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    if category_id not in EXPENSE_CATEGORIES:
        await _send(callback, tr.t("error.generic"))
        return
    await state.update_data(category_id=category_id)
    await state.set_state(ExpenseFSM.description)
    await _send(callback, tr.t("expense.ask_description"))


@router.message(ExpenseFSM.description)
async def expense_description(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    data = await state.get_data()
    await state.clear()
    command = RecordExpenseCommand(
        actor=actor,  # type: ignore[arg-type]
        amount=Money(int(data["amount_minor"])),
        category_id=int(data["category_id"]),
        description=message.text or "",
        event_at=container.clock.now(),
    )
    try:
        result = container.record_expense.execute(command)
    except PermissionDeniedError:
        await message.answer(tr.t("error.permission_denied"))
        return
    except (ApplicationError, DomainError):
        await message.answer(tr.t("error.generic"))
        return
    text = tr.t("expense.recorded", ref=result.reference_no)
    if result.overspent:
        text += "\n" + tr.t("expense.overspent_warning")
    await message.answer(text, reply_markup=main_menu(actor, tr))


@router.callback_query(F.data == "sec:recent_entries")
async def recent_entries(callback: CallbackQuery, actor: StaffUser | None, tr: Translator) -> None:
    # Listing/reversal UI is a follow-up milestone; the use cases already exist.
    await _send(callback, tr.t("common.done"), reply_markup=main_menu(actor, tr))


# --------------------------------------------------------------------------- #
# Admin: manage staff
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:manage_staff")
async def start_register_staff(callback: CallbackQuery, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.USER_MANAGE):
        await _send(callback, tr.t("error.permission_denied"))
        return
    await state.set_state(RegisterStaffFSM.telegram_id)
    await _send(callback, tr.t("staff.ask_telegram_id"))


@router.message(RegisterStaffFSM.telegram_id)
async def staff_telegram_id(message: Message, state: FSMContext, tr: Translator) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(tr.t("error.invalid_amount"))
        return
    await state.update_data(telegram_id=int(text))
    await state.set_state(RegisterStaffFSM.role)
    await message.answer(tr.t("staff.ask_role"), reply_markup=role_menu(tr))


@router.callback_query(RegisterStaffFSM.role, F.data.startswith("role:"))
async def staff_role(callback: CallbackQuery, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    choice = callback.data.split(":", 1)[1]
    role = SUPER_ADMIN_ROLE if choice == "admin" else TREASURER_ROLE
    data = await state.get_data()
    await state.clear()
    command = RegisterStaffCommand(actor=actor, telegram_id=int(data["telegram_id"]), role=role)  # type: ignore[arg-type]
    try:
        container.register_staff.execute(command)
    except PermissionDeniedError:
        await _send(callback, tr.t("error.permission_denied"))
        return
    except ApplicationError:
        await _send(callback, tr.t("staff.already_registered"))
        return
    await _send(callback, tr.t("staff.registered"), reply_markup=main_menu(actor, tr))


# --------------------------------------------------------------------------- #
# Admin: configure donation account
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:configure_account")
async def start_configure_account(callback: CallbackQuery, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.ACCOUNT_MANAGE):
        await _send(callback, tr.t("error.permission_denied"))
        return
    await state.set_state(ConfigureAccountFSM.label)
    await _send(callback, tr.t("account.label", label="?"))


@router.message(ConfigureAccountFSM.label)
async def account_label(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(label=(message.text or "").strip())
    await state.set_state(ConfigureAccountFSM.account_type)
    await message.answer(tr.t("account.title"), reply_markup=account_type_menu(tr))


@router.callback_query(ConfigureAccountFSM.account_type, F.data.startswith("acct:"))
async def account_type(callback: CallbackQuery, state: FSMContext, tr: Translator) -> None:
    await state.update_data(account_type=callback.data.split(":", 1)[1])
    await state.set_state(ConfigureAccountFSM.value)
    await _send(callback, tr.t("account.number", value="?"))


@router.message(ConfigureAccountFSM.value)
async def account_value(message: Message, state: FSMContext, tr: Translator) -> None:
    await state.update_data(value=(message.text or "").strip())
    await state.set_state(ConfigureAccountFSM.holder)
    await message.answer(tr.t("account.holder", holder="?"), reply_markup=skip_menu(tr))


async def _finalize_account(
    event: Message | CallbackQuery, state: FSMContext, container: Container,
    actor: StaffUser | None, tr: Translator, holder: str | None,
) -> None:
    data = await state.get_data()
    await state.clear()
    command = ConfigureDonationAccountCommand(
        actor=actor,  # type: ignore[arg-type]
        label=data["label"],
        account_type=AccountType(data["account_type"]),
        account_value=data["value"],
        holder_name=holder,
    )
    try:
        container.configure_account.execute(command)
    except PermissionDeniedError:
        await _send(event, tr.t("error.permission_denied"))
        return
    except (ApplicationError, DomainError):
        await _send(event, tr.t("error.generic"))
        return
    await _send(event, tr.t("common.done"), reply_markup=main_menu(actor, tr))


@router.message(ConfigureAccountFSM.holder)
async def account_holder_text(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finalize_account(message, state, container, actor, tr, holder=message.text)


@router.callback_query(ConfigureAccountFSM.holder, F.data == "skip")
async def account_holder_skip(callback: CallbackQuery, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finalize_account(callback, state, container, actor, tr, holder=None)


# --------------------------------------------------------------------------- #
# Admin: audit log (view UI is a follow-up milestone)
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "sec:audit_log")
async def audit_log(callback: CallbackQuery, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.AUDIT_VIEW):
        await _send(callback, tr.t("error.permission_denied"))
        return
    await _send(callback, tr.t("common.done"), reply_markup=main_menu(actor, tr))
