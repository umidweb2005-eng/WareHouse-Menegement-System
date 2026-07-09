"""Tests for the framework-independent presentation helpers (i18n, menu,
formatting, parsing) used by the Telegram adapter."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import _appsupport as app

from donation_bot.adapters.telegram.formatting import (
    format_account,
    format_money,
    format_report,
    format_statistics,
)
from donation_bot.adapters.telegram.menu import (
    SECTION_LABEL_KEY,
    Section,
    main_sections,
)
from donation_bot.adapters.telegram.parsing import AmountParseError, parse_amount_to_money
from donation_bot.application.reports.models import LedgerTotals, PeriodReport, Statistics
from donation_bot.domain.accounts.entities import AccountType, DonationAccount
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import Translator, get_translator

UTC = timezone.utc


class I18nTests(unittest.TestCase):
    def test_known_key_and_formatting(self) -> None:
        tr = get_translator("uz")
        self.assertNotIn("<", tr.t("menu.donate"))
        self.assertIn("#7", tr.t("donation.recorded", ref=7))

    def test_missing_key_is_visible(self) -> None:
        self.assertEqual(Translator().t("does.not.exist"), "<does.not.exist>")

    def test_unknown_locale_falls_back_to_uz(self) -> None:
        self.assertEqual(get_translator("fr").locale, "uz")


class MenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_public_sees_only_public_sections(self) -> None:
        sections = main_sections(None)
        self.assertEqual(sections, [Section.DONATE, Section.STATISTICS, Section.REPORTS])

    def test_treasurer_sees_recording_sections(self) -> None:
        sections = main_sections(self.ctx.treasurer)
        self.assertIn(Section.RECORD_DONATION, sections)
        self.assertIn(Section.RECORD_EXPENSE, sections)
        self.assertNotIn(Section.MANAGE_STAFF, sections)

    def test_admin_sees_governance_sections(self) -> None:
        sections = main_sections(self.ctx.admin)
        self.assertIn(Section.MANAGE_STAFF, sections)
        self.assertIn(Section.CONFIGURE_ACCOUNT, sections)
        self.assertIn(Section.AUDIT_LOG, sections)

    def test_every_section_has_a_label_key(self) -> None:
        for section in Section:
            self.assertIn(section, SECTION_LABEL_KEY)


class FormattingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tr = get_translator("uz")

    def test_money_grouping_and_suffix(self) -> None:
        self.assertEqual(format_money(Money(500000), self.tr), "5 000 so'm")  # 5000 so'm
        self.assertEqual(format_money(Money(-500000), self.tr), "-5 000 so'm")

    def test_money_with_tiyin_remainder(self) -> None:
        self.assertEqual(format_money(Money(500050), self.tr), "5 000.50 so'm")

    def test_report_lists_usage_descriptions(self) -> None:
        totals = LedgerTotals(Money(1000000), Money(300000), 2, 1)
        from donation_bot.application.reports.models import ExpenseLine

        report = PeriodReport(
            label="2026-05",
            totals=totals,
            expense_lines=(
                ExpenseLine(
                    reference_no=3,
                    amount=Money(300000),
                    category_id=1,
                    description="Aid to family",
                    event_at=datetime(2026, 5, 1, tzinfo=UTC),
                ),
            ),
        )
        text = format_report(report, self.tr)
        self.assertIn("2026-05", text)
        self.assertIn("Aid to family", text)
        self.assertIn("#3", text)

    def test_statistics_render(self) -> None:
        z = LedgerTotals.empty()
        stats = Statistics(
            generated_at=datetime(2026, 5, 1, tzinfo=UTC),
            today=z,
            this_month=z,
            this_year=z,
            all_time=z,
        )
        self.assertIn("Statistika", format_statistics(stats, self.tr))

    def test_account_rendering(self) -> None:
        self.assertIn("sozlanmagan", format_account(None, self.tr))
        acc = DonationAccount(
            label="Main",
            account_type=AccountType.CARD,
            account_value="8600...",
            created_by="a",
            created_at=datetime(2026, 5, 1, tzinfo=UTC),
        )
        text = format_account(acc, self.tr)
        self.assertIn("Main", text)
        self.assertIn("8600...", text)


class ParsingTests(unittest.TestCase):
    def test_parses_grouped_amount(self) -> None:
        self.assertEqual(parse_amount_to_money("5 000").amount_minor, 500000)
        self.assertEqual(parse_amount_to_money("1,000,000").amount_minor, 100000000)

    def test_rejects_non_numeric(self) -> None:
        for bad in ("", "abc", "5.5", "-100"):
            with self.assertRaises(AmountParseError):
                parse_amount_to_money(bad)


if __name__ == "__main__":
    unittest.main()
