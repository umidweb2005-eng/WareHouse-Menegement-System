"""Reply keyboards (aiogram). Large, persistent bottom keyboards.

Button text comes from the translator; the main-menu structure comes from the
menu logic. Reply keyboards are used throughout for a Telegram-first, tap-friendly
UX; handlers route on the button text (see :mod:`labels`).
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from donation_bot.adapters.telegram.menu import SECTION_LABEL_KEY, main_sections
from donation_bot.adapters.telegram.support import EXPENSE_CATEGORIES
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator


def _kb(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
    )


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main_menu(actor: StaffUser | None, tr: Translator) -> ReplyKeyboardMarkup:
    labels = [tr.t(SECTION_LABEL_KEY[s]) for s in main_sections(actor)]
    return _kb(_chunk(labels, 2))


def reports_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("reports.today"), tr.t("reports.month")],
            [tr.t("reports.year"), tr.t("reports.all_time")],
            [tr.t("common.back")],
        ]
    )


def source_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("donation.source_cash"), tr.t("donation.source_bank")],
            [tr.t("common.cancel")],
        ]
    )


def category_menu(tr: Translator) -> ReplyKeyboardMarkup:
    names = list(EXPENSE_CATEGORIES.values())
    return _kb(_chunk(names, 2) + [[tr.t("common.cancel")]])


def role_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("staff.role_treasurer"), tr.t("staff.role_admin")],
            [tr.t("common.cancel")],
        ]
    )


def account_type_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("account.type_card"), tr.t("account.type_bank")],
            [tr.t("account.type_wallet")],
            [tr.t("common.cancel")],
        ]
    )


def confirm_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb([[tr.t("common.confirm")], [tr.t("common.cancel")]])


def skip_cancel_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb([[tr.t("common.skip")], [tr.t("common.cancel")]])


def cancel_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb([[tr.t("common.cancel")]])
