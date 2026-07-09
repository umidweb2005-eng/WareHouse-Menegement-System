"""Presentation formatting (framework-independent).

Turns domain/application values into localized display text. No aiogram
dependency, so it is fully unit-testable. Money is formatted for display only
here; the core always works in integer minor units.
"""

from __future__ import annotations

from donation_bot.application.reports.models import PeriodReport, Statistics
from donation_bot.domain.accounts.entities import DonationAccount
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import Translator


def format_money(money: Money, translator: Translator) -> str:
    per = money.currency.minor_per_major
    exp = money.currency.exponent
    minor = money.amount_minor
    sign = "-" if minor < 0 else ""
    major, remainder = divmod(abs(minor), per)
    grouped = f"{major:,}".replace(",", " ")  # 5000 -> "5 000"
    suffix = translator.t("money.suffix")
    if remainder and exp > 0:
        return f"{sign}{grouped}.{remainder:0{exp}d} {suffix}"
    return f"{sign}{grouped} {suffix}"


def format_report(report: PeriodReport, translator: Translator) -> str:
    m = lambda money: format_money(money, translator)  # noqa: E731
    lines = [
        translator.t("report.title", label=report.label),
        translator.t("report.total_in", amount=m(report.totals.total_in)),
        translator.t("report.total_out", amount=m(report.totals.total_out)),
        translator.t("report.net", amount=m(report.totals.net)),
        translator.t(
            "report.counts",
            donations=report.totals.donation_count,
            expenses=report.totals.expense_count,
        ),
    ]
    if report.expense_lines:
        lines.append(translator.t("report.usage_header"))
        for line in report.expense_lines:
            lines.append(
                translator.t(
                    "report.usage_line",
                    ref=line.reference_no,
                    amount=m(line.amount),
                    desc=line.description,
                )
            )
    else:
        lines.append(translator.t("report.no_expenses"))
    return "\n".join(lines)


def format_statistics(stats: Statistics, translator: Translator) -> str:
    m = lambda money: format_money(money, translator)  # noqa: E731
    return "\n".join(
        [
            translator.t("stats.title"),
            translator.t("stats.today", amount=m(stats.today.net)),
            translator.t("stats.this_month", amount=m(stats.this_month.net)),
            translator.t("stats.this_year", amount=m(stats.this_year.net)),
            translator.t("stats.all_time", amount=m(stats.all_time.net)),
        ]
    )


def format_account(account: DonationAccount | None, translator: Translator) -> str:
    if account is None:
        return translator.t("account.none")
    if account.is_disabled:
        return translator.t("account.disabled")
    lines = [
        translator.t("account.title"),
        translator.t("account.label", label=account.label),
        translator.t("account.number", value=account.account_value),
    ]
    if account.holder_name:
        lines.append(translator.t("account.holder", holder=account.holder_name))
    return "\n".join(lines)


def format_donation_info(account: DonationAccount | None, translator: Translator) -> str:
    """The public "how to donate" screen: title, the active account, privacy note."""
    return "\n\n".join(
        [
            translator.t("donate.title"),
            translator.t("donate.instructions"),
            format_account(account, translator),
            translator.t("donate.privacy"),
        ]
    )


def format_about(translator: Translator) -> str:
    return translator.t("about.text")
