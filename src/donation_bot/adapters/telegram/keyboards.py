"""Reply keyboards (aiogram): large, always-visible bottom keyboards.

Every keyboard is built with ``resize_keyboard=True``, ``one_time_keyboard=False``
and ``is_persistent=True`` so it stays docked under the conversation and never
collapses. The main menu is rendered two buttons per row (per the product spec);
FSM forms temporarily replace it with a compact navigation row (Back + Cancel).
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from donation_bot.adapters.telegram.menu import SECTION_LABEL_KEY, main_sections
from donation_bot.adapters.telegram.support import EXPENSE_CATEGORIES
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator


def _kb(rows: list[list[str]], *, placeholder: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
        input_field_placeholder=placeholder,
    )


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _nav_row(tr: Translator) -> list[str]:
    """Back + Cancel — the standard FSM navigation row."""
    return [tr.t("common.back"), tr.t("common.cancel")]


# --------------------------------------------------------------------------- #
# Main menu (always visible outside flows)
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# FSM form keyboards (Back + Cancel always present)
# --------------------------------------------------------------------------- #
def form_menu(tr: Translator, *, placeholder: str | None = None) -> ReplyKeyboardMarkup:
    """Text-input step: only Back + Cancel."""
    return _kb([_nav_row(tr)], placeholder=placeholder)


def source_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("donation.source_cash"), tr.t("donation.source_bank")],
            _nav_row(tr),
        ]
    )


def category_menu(tr: Translator) -> ReplyKeyboardMarkup:
    names = list(EXPENSE_CATEGORIES.values())
    return _kb(_chunk(names, 2) + [_nav_row(tr)])


def role_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("staff.role_treasurer"), tr.t("staff.role_admin")],
            _nav_row(tr),
        ]
    )


def account_type_menu(tr: Translator) -> ReplyKeyboardMarkup:
    return _kb(
        [
            [tr.t("account.type_card"), tr.t("account.type_bank")],
            [tr.t("account.type_wallet")],
            _nav_row(tr),
        ]
    )


def note_menu(tr: Translator) -> ReplyKeyboardMarkup:
    """Optional-note step: Skip on its own row, then Back + Cancel."""
    return _kb([[tr.t("common.skip")], _nav_row(tr)])


def confirm_menu(tr: Translator) -> ReplyKeyboardMarkup:
    """Confirmation step: Confirm on its own row, then Back + Cancel."""
    return _kb([[tr.t("common.confirm")], _nav_row(tr)])
