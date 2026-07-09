"""Tests for the QueryAuditLog use case and audit formatting."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import _appsupport as app

from donation_bot.adapters.telegram.formatting import format_audit
from donation_bot.application.audit.models import DONATION_RECORDED, AuditEntry
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import PermissionDeniedError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money
from donation_bot.infrastructure.i18n.translator import get_translator


class QueryAuditLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def _record(self, minor: int) -> None:
        self.ctx.record_donation.execute(
            RecordDonationCommand(
                actor=self.ctx.treasurer,
                amount=Money(minor),
                source=DonationSource.CASH,
                event_at=self.ctx.clock.now(),
            )
        )

    def test_admin_sees_recent_entries_newest_first(self) -> None:
        self._record(1000)
        self._record(2000)
        entries = self.ctx.query_audit_log.execute(self.ctx.admin)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].action, DONATION_RECORDED)
        # newest first: the second donation's reference is higher
        self.assertGreater(entries[0].entity_ref, entries[1].entity_ref)

    def test_limit_is_respected(self) -> None:
        for _ in range(5):
            self._record(100)
        self.assertEqual(len(self.ctx.query_audit_log.execute(self.ctx.admin, limit=3)), 3)

    def test_treasurer_and_public_denied(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.query_audit_log.execute(self.ctx.treasurer)
        with self.assertRaises(PermissionDeniedError):
            self.ctx.query_audit_log.execute(None)


class FormatAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tr = get_translator("uz")

    def test_empty(self) -> None:
        self.assertIn(self.tr.t("audit.empty"), format_audit([], self.tr))

    def test_entries_render_localized_action_and_ref(self) -> None:
        entry = AuditEntry(
            action=DONATION_RECORDED,
            entity_type="ledger_entry",
            actor_user_id="t1",
            created_at=datetime(2026, 5, 1, 9, 30, tzinfo=timezone.utc),
            entity_ref=42,
        )
        text = format_audit([entry], self.tr)
        self.assertIn(self.tr.t("audit.action.donation.recorded"), text)
        self.assertIn("#42", text)
        self.assertIn("2026-05-01", text)


if __name__ == "__main__":
    unittest.main()
