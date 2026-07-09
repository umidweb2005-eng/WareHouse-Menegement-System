"""Public handlers: donation info / account, statistics, reports.

All read-only and available to everyone (the use cases treat these as public).
Menu-entry handlers use ``StateFilter(None)`` so they never interfere with an
active treasurer/admin flow.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from donation_bot.adapters.telegram import labels
from donation_bot.adapters.telegram.formatting import (
    format_donation_info,
    format_report,
    format_statistics,
)
from donation_bot.adapters.telegram.keyboards import main_menu, reports_menu
from donation_bot.adapters.telegram.support import local_today
from donation_bot.application.reports.models import PeriodReport
from donation_bot.composition.container import Container
from donation_bot.domain.access.entities import StaffUser
from donation_bot.infrastructure.i18n.translator import Translator

router = Router(name="public")


@router.message(StateFilter(None), F.text == labels.DONATE)
async def show_donate(message: Message, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    account = container.get_active_account.execute(actor=actor)
    await message.answer(format_donation_info(account, tr), reply_markup=main_menu(actor, tr))


@router.message(StateFilter(None), F.text == labels.STATISTICS)
async def show_statistics(message: Message, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    stats = container.reports.statistics(actor=actor)
    await message.answer(format_statistics(stats, tr), reply_markup=main_menu(actor, tr))


@router.message(StateFilter(None), F.text == labels.REPORTS)
async def choose_report(message: Message, tr: Translator) -> None:
    await message.answer(tr.t("reports.choose_period"), reply_markup=reports_menu(tr))


def _report_for(container: Container, actor: StaffUser | None, period_label: str) -> PeriodReport:
    today = local_today(container.clock, container.settings.app.org_timezone)
    if period_label == labels.REP_TODAY:
        return container.reports.daily_report(today, actor=actor)
    if period_label == labels.REP_MONTH:
        return container.reports.monthly_report(today.year, today.month, actor=actor)
    if period_label == labels.REP_YEAR:
        return container.reports.yearly_report(today.year, actor=actor)
    return container.reports.total_report(actor=actor)


@router.message(
    StateFilter(None),
    F.text.in_({labels.REP_TODAY, labels.REP_MONTH, labels.REP_YEAR, labels.REP_ALL}),
)
async def show_report(message: Message, container: Container, actor: StaffUser | None, tr: Translator) -> None:
    report = _report_for(container, actor, message.text or "")
    # Keep the period keyboard so the user can view another period quickly.
    await message.answer(format_report(report, tr), reply_markup=reports_menu(tr))
