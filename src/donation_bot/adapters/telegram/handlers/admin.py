"""Super Admin flows: register staff, change the donation account, view audit log.

Guided FSMs; permissions are pre-checked for UX and re-enforced by the use cases.
Cancellation is handled globally by the nav router.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from donation_bot.adapters.telegram import labels
from donation_bot.adapters.telegram.formatting import format_audit
from donation_bot.adapters.telegram.keyboards import (
    account_type_menu,
    cancel_menu,
    main_menu,
    role_menu,
    skip_cancel_menu,
)
from donation_bot.adapters.telegram.states import ConfigureAccountFSM, RegisterStaffFSM
from donation_bot.application.access.register_staff import RegisterStaffCommand
from donation_bot.application.errors import (
    PermissionDeniedError,
    StaffAlreadyRegisteredError,
)
from donation_bot.application.settings.configure_account import (
    ConfigureDonationAccountCommand,
)
from donation_bot.composition.container import Container
from donation_bot.domain.access.entities import SUPER_ADMIN_ROLE, TREASURER_ROLE, StaffUser
from donation_bot.domain.access.permissions import Permission
from donation_bot.domain.accounts.entities import AccountType
from donation_bot.domain.errors import DomainError
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="admin")

_ACCOUNT_TYPE_BY_LABEL = {
    labels.ACC_CARD: AccountType.CARD,
    labels.ACC_BANK: AccountType.BANK_ACCOUNT,
    labels.ACC_WALLET: AccountType.WALLET,
}


def _can(actor: StaffUser | None, permission: Permission) -> bool:
    return actor is not None and actor.has_permission(permission)


# --------------------------------------------------------------------------- #
# Register staff
# --------------------------------------------------------------------------- #
@router.message(StateFilter(None), F.text == labels.MANAGE_STAFF)
async def staff_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.USER_MANAGE):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await state.set_state(RegisterStaffFSM.telegram_id)
    await message.answer(tr.t("staff.ask_telegram_id"), reply_markup=cancel_menu(tr))


@router.message(RegisterStaffFSM.telegram_id)
async def staff_telegram_id(message: Message, state: FSMContext, tr: Translator) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(tr.t("staff.invalid_id"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(telegram_id=int(text))
    await state.set_state(RegisterStaffFSM.role)
    await message.answer(tr.t("staff.ask_role"), reply_markup=role_menu(tr))


@router.message(RegisterStaffFSM.role, F.text.in_({labels.ROLE_TREASURER, labels.ROLE_ADMIN}))
async def staff_role(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    role = SUPER_ADMIN_ROLE if message.text == labels.ROLE_ADMIN else TREASURER_ROLE
    data = await state.get_data()
    await state.clear()
    command = RegisterStaffCommand(
        actor=actor,  # type: ignore[arg-type]  # guarded at flow start
        telegram_id=int(data["telegram_id"]),
        role=role,
    )
    try:
        container.register_staff.execute(command)
    except PermissionDeniedError:
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    except StaffAlreadyRegisteredError:
        await message.answer(tr.t("staff.already_registered"), reply_markup=main_menu(actor, tr))
        return
    except DomainError:
        await message.answer(tr.t("error.generic"), reply_markup=main_menu(actor, tr))
        return
    await message.answer(tr.t("staff.registered"), reply_markup=main_menu(actor, tr))


@router.message(RegisterStaffFSM.role)
async def staff_role_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("staff.ask_role"), reply_markup=role_menu(tr))


# --------------------------------------------------------------------------- #
# Change donation account
# --------------------------------------------------------------------------- #
@router.message(StateFilter(None), F.text == labels.CONFIGURE_ACCOUNT)
async def account_start(message: Message, state: FSMContext, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.ACCOUNT_MANAGE):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    await state.set_state(ConfigureAccountFSM.label)
    await message.answer(tr.t("account.ask_label"), reply_markup=cancel_menu(tr))


@router.message(ConfigureAccountFSM.label)
async def account_label(message: Message, state: FSMContext, tr: Translator) -> None:
    label = (message.text or "").strip()
    if not label:
        await message.answer(tr.t("error.empty_text"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(label=label)
    await state.set_state(ConfigureAccountFSM.account_type)
    await message.answer(tr.t("account.ask_type"), reply_markup=account_type_menu(tr))


@router.message(ConfigureAccountFSM.account_type, F.text.in_(set(_ACCOUNT_TYPE_BY_LABEL)))
async def account_type(message: Message, state: FSMContext, tr: Translator) -> None:
    chosen = _ACCOUNT_TYPE_BY_LABEL[message.text or ""]
    await state.update_data(account_type=chosen.value)
    await state.set_state(ConfigureAccountFSM.value)
    await message.answer(tr.t("account.ask_value"), reply_markup=cancel_menu(tr))


@router.message(ConfigureAccountFSM.account_type)
async def account_type_retry(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("account.ask_type"), reply_markup=account_type_menu(tr))


@router.message(ConfigureAccountFSM.value)
async def account_value(message: Message, state: FSMContext, tr: Translator) -> None:
    value = (message.text or "").strip()
    if not value:
        await message.answer(tr.t("error.empty_text"), reply_markup=cancel_menu(tr))
        return
    await state.update_data(value=value)
    await state.set_state(ConfigureAccountFSM.holder)
    await message.answer(tr.t("account.ask_holder"), reply_markup=skip_cancel_menu(tr))


async def _finish_account(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator, holder: str | None) -> None:
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
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    except DomainError:
        await message.answer(tr.t("error.generic"), reply_markup=main_menu(actor, tr))
        return
    await message.answer(tr.t("account.updated"), reply_markup=main_menu(actor, tr))


@router.message(ConfigureAccountFSM.holder, F.text == labels.SKIP)
async def account_holder_skip(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finish_account(message, state, container, actor, tr, holder=None)


@router.message(ConfigureAccountFSM.holder)
async def account_holder_text(message: Message, state: FSMContext, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    await _finish_account(message, state, container, actor, tr, holder=(message.text or "").strip() or None)


# --------------------------------------------------------------------------- #
# Audit log
# --------------------------------------------------------------------------- #
@router.message(StateFilter(None), F.text == labels.AUDIT_LOG)
async def show_audit(message: Message, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    if not _can(actor, Permission.AUDIT_VIEW):
        await message.answer(tr.t("error.permission_denied"), reply_markup=main_menu(actor, tr))
        return
    entries = container.query_audit_log.execute(actor)
    await message.answer(format_audit(entries, tr), reply_markup=main_menu(actor, tr))
