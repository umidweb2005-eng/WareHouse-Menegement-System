"""Presentation formatting (framework-independent).

Turns domain/application values into localized display text. No aiogram
dependency, so it is fully unit-testable. Money is formatted for display only
here; the core always works in integer minor units.
"""

from __future__ import annotations

from collections.abc import Sequence
from zoneinfo import ZoneInfo

from donation_bot.application.audit.models import AuditEntry
from donation_bot.application.reports.models import EntrySummary, PeriodReport, Statistics
from donation_bot.domain.accounts.entities import DonationAccount
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import Translator

_SOURCE_KEY: dict[DonationSource, str] = {
    DonationSource.CASH: "donation.source_cash",
    DonationSource.BANK_MANUAL: "donation.source_bank",
    DonationSource.BANK_API: "donation.source_bank",
}


def source_label(source: DonationSource, translator: Translator) -> str:
    return translator.t(_SOURCE_KEY[source])


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


def format_recent_entries(
    entries: Sequence[EntrySummary], translator: Translator, org_timezone: str
) -> str:
    """Staff-only recent-entries list, dates shown in the organization time zone."""
    if not entries:
        return translator.t("recent.title") + "\n" + translator.t("recent.empty")
    zone = ZoneInfo(org_timezone)
    lines = [translator.t("recent.title")]
    for entry in entries:
        date = entry.event_at.astimezone(zone).strftime("%d.%m.%Y")
        reversed_mark = translator.t("recent.reversed_mark") if entry.is_reversed else ""
        amount = format_money(entry.amount, translator)
        if entry.kind == "donation":
            lines.append(
                translator.t(
                    "recent.line_donation",
                    ref=entry.reference_no,
                    amount=amount,
                    date=date,
                    reversed=reversed_mark,
                )
            )
        else:
            lines.append(
                translator.t(
                    "recent.line_expense",
                    ref=entry.reference_no,
                    amount=amount,
                    date=date,
                    desc=entry.description or "",
                    reversed=reversed_mark,
                )
            )
    return "\n".join(lines)


def format_donation_confirmation(
    amount: Money, source: DonationSource, note: str | None, translator: Translator
) -> str:
    summary = translator.t(
        "donation.summary",
        amount=format_money(amount, translator),
        source=source_label(source, translator),
        note=note if (note and note.strip()) else translator.t("donation.note_none"),
    )
    return translator.t("donation.confirm_title") + "\n\n" + summary


def format_expense_confirmation(
    amount: Money, category_name: str, description: str, translator: Translator
) -> str:
    summary = translator.t(
        "expense.summary",
        amount=format_money(amount, translator),
        category=category_name,
        desc=description,
    )
    return translator.t("expense.confirm_title") + "\n\n" + summary


def _action_label(action: str, translator: Translator) -> str:
    label = translator.t(f"audit.action.{action}")
    return action if label.startswith("<") else label  # fall back to raw code


def format_audit(entries: Sequence[AuditEntry], translator: Translator) -> str:
    if not entries:
        return translator.t("audit.title") + "\n" + translator.t("audit.empty")
    lines = [translator.t("audit.title")]
    for entry in entries:
        ref = f" #{entry.entity_ref}" if entry.entity_ref is not None else ""
        when = entry.created_at.strftime("%Y-%m-%d %H:%M")  # UTC
        lines.append(
            translator.t(
                "audit.line",
                time=when,
                action=_action_label(entry.action, translator),
                ref=ref,
            )
        )
    return "\n".join(lines)
