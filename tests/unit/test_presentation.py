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
from donation_bot.adapters.telegram import labels
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

    def test_treasurer_sees_recording_and_recent_sections(self) -> None:
        sections = main_sections(self.ctx.treasurer)
        self.assertIn(Section.RECORD_DONATION, sections)
        self.assertIn(Section.RECORD_EXPENSE, sections)
        self.assertIn(Section.RECENT_ENTRIES, sections)
        self.assertNotIn(Section.MANAGE_STAFF, sections)

    def test_admin_menu_matches_spec_order(self) -> None:
        # Full admin menu, in the exact display order (rendered two per row).
        self.assertEqual(
            main_sections(self.ctx.admin),
            [
                Section.DONATE,
                Section.STATISTICS,
                Section.REPORTS,
                Section.RECORD_DONATION,
                Section.RECORD_EXPENSE,
                Section.RECENT_ENTRIES,
                Section.MANAGE_STAFF,
                Section.CONFIGURE_ACCOUNT,
                Section.AUDIT_LOG,
            ],
        )

    def test_every_section_has_a_label_key(self) -> None:
        for section in Section:
            self.assertIn(section, SECTION_LABEL_KEY)

    def test_labels_match_catalog(self) -> None:
        tr = get_translator("uz")
        self.assertEqual(labels.DONATE, tr.t("menu.donate"))
        self.assertEqual(labels.CANCEL, tr.t("common.cancel"))
        self.assertEqual(labels.REP_TODAY, tr.t("reports.today"))
        # every visible menu label is routable back to a section label
        self.assertEqual(labels.RECORD_DONATION, tr.t("menu.record_donation"))


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

    def test_donation_info_with_account(self) -> None:
        from donation_bot.adapters.telegram.formatting import format_donation_info

        acc = DonationAccount(
            label="Main card",
            account_type=AccountType.CARD,
            account_value="8600 0000",
            created_by="a",
            created_at=datetime(2026, 5, 1, tzinfo=UTC),
        )
        text = format_donation_info(acc, self.tr)
        self.assertIn("8600 0000", text)
        self.assertIn(self.tr.t("donate.privacy"), text)

    def test_donation_info_without_account(self) -> None:
        from donation_bot.adapters.telegram.formatting import format_donation_info

        text = format_donation_info(None, self.tr)
        self.assertIn(self.tr.t("account.none"), text)
        self.assertIn(self.tr.t("donate.privacy"), text)

    def test_donation_confirmation(self) -> None:
        from donation_bot.adapters.telegram.formatting import format_donation_confirmation
        from donation_bot.domain.ledger.entities import DonationSource

        text = format_donation_confirmation(Money(500000), DonationSource.CASH, None, self.tr)
        self.assertIn("5 000 so'm", text)
        self.assertIn(self.tr.t("donation.source_cash"), text)
        self.assertIn(self.tr.t("donation.note_none"), text)  # no note -> "yo'q"

        with_note = format_donation_confirmation(
            Money(500000), DonationSource.BANK_MANUAL, "juma", self.tr
        )
        self.assertIn("juma", with_note)
        self.assertIn(self.tr.t("donation.source_bank"), with_note)

    def test_expense_confirmation(self) -> None:
        from donation_bot.adapters.telegram.formatting import format_expense_confirmation

        text = format_expense_confirmation(Money(300000), "Kommunal", "Svet uchun", self.tr)
        self.assertIn("3 000 so'm", text)
        self.assertIn("Kommunal", text)
        self.assertIn("Svet uchun", text)


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
