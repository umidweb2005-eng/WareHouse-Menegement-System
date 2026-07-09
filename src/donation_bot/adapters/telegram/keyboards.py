"""Inline keyboards (aiogram). Text comes from the translator; structure from the
menu logic in :mod:`donation_bot.adapters.telegram.menu`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from donation_bot.adapters.telegram.menu import SECTION_LABEL_KEY, main_sections
from donation_bot.adapters.telegram.support import EXPENSE_CATEGORIES
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator


def _rows(*buttons: InlineKeyboardButton) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])


def main_menu(actor: StaffUser | None, tr: Translator) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=tr.t(SECTION_LABEL_KEY[s]), callback_data=f"sec:{s.value}")
        for s in main_sections(actor)
    ]
    return _rows(*buttons)


def back_menu(tr: Translator) -> InlineKeyboardMarkup:
    return _rows(InlineKeyboardButton(text=tr.t("common.back"), callback_data="menu"))


def period_menu(tr: Translator) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr.t("reports.today"), callback_data="rep:today"),
                InlineKeyboardButton(text=tr.t("reports.month"), callback_data="rep:month"),
            ],
            [
                InlineKeyboardButton(text=tr.t("reports.year"), callback_data="rep:year"),
                InlineKeyboardButton(text=tr.t("reports.all_time"), callback_data="rep:all"),
            ],
            [InlineKeyboardButton(text=tr.t("common.back"), callback_data="menu")],
        ]
    )


def source_menu(tr: Translator) -> InlineKeyboardMarkup:
    return _rows(
        InlineKeyboardButton(text=tr.t("donation.source_cash"), callback_data="src:cash"),
        InlineKeyboardButton(text=tr.t("donation.source_bank"), callback_data="src:bank"),
    )


def skip_menu(tr: Translator) -> InlineKeyboardMarkup:
    return _rows(
        InlineKeyboardButton(text=tr.t("common.skip"), callback_data="skip"),
        InlineKeyboardButton(text=tr.t("common.cancel"), callback_data="menu"),
    )


def category_menu(tr: Translator) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=name, callback_data=f"cat:{cid}")
        for cid, name in EXPENSE_CATEGORIES.items()
    ]
    return _rows(*buttons)


def role_menu(tr: Translator) -> InlineKeyboardMarkup:
    return _rows(
        InlineKeyboardButton(text=tr.t("staff.role_treasurer"), callback_data="role:treasurer"),
        InlineKeyboardButton(text=tr.t("staff.role_admin"), callback_data="role:admin"),
    )


def account_type_menu(tr: Translator) -> InlineKeyboardMarkup:
    return _rows(
        InlineKeyboardButton(text="Karta", callback_data="acct:card"),
        InlineKeyboardButton(text="Bank hisob", callback_data="acct:bank_account"),
        InlineKeyboardButton(text="Hamyon", callback_data="acct:wallet"),
    )
