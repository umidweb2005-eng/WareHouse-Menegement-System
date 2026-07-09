"""AddAnnotation / RedactAnnotation use-case tests (privacy-focused)."""

from __future__ import annotations

import unittest

import _appsupport as app

from donation_bot.application.annotations.add_annotation import AddAnnotationCommand
from donation_bot.application.annotations.redact_annotation import RedactAnnotationCommand
from donation_bot.application.audit.models import ANNOTATION_REDACTED
from donation_bot.application.donations.record_donation import RecordDonationCommand
from donation_bot.application.errors import (
    AnnotationNotFoundError,
    EntryNotFoundError,
    PermissionDeniedError,
)
from donation_bot.domain.annotations.entities import REDACTION_TOMBSTONE
from donation_bot.domain.errors import DomainError
from donation_bot.domain.ledger.entities import DonationSource
from donation_bot.domain.money import Money


class AnnotationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()
        self.donation = self.ctx.record_donation.execute(
            RecordDonationCommand(
                actor=self.ctx.treasurer,
                amount=Money(1000),
                source=DonationSource.CASH,
                event_at=self.ctx.clock.now(),
            )
        )

    def test_treasurer_adds_private_note(self) -> None:
        result = self.ctx.add_annotation.execute(
            AddAnnotationCommand(
                actor=self.ctx.treasurer, reference_no=self.donation.reference_no, text="Friday box"
            )
        )
        ann = self.ctx.store.annotations[result.annotation_id]
        self.assertEqual(ann.content, "Friday box")
        self.assertFalse(ann.is_redacted)

    def test_add_to_unknown_reference_raises(self) -> None:
        with self.assertRaises(EntryNotFoundError):
            self.ctx.add_annotation.execute(
                AddAnnotationCommand(actor=self.ctx.treasurer, reference_no=999, text="x")
            )

    def test_empty_note_rejected(self) -> None:
        with self.assertRaises(DomainError):
            self.ctx.add_annotation.execute(
                AddAnnotationCommand(
                    actor=self.ctx.treasurer, reference_no=self.donation.reference_no, text="   "
                )
            )

    def test_non_treasurer_cannot_annotate(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.add_annotation.execute(
                AddAnnotationCommand(
                    actor=self.ctx.plain_user, reference_no=self.donation.reference_no, text="x"
                )
            )

    def test_admin_redacts_pii_and_audit_has_no_leaked_text(self) -> None:
        leaked = "donated by Kamola, phone 90-123-45-67"
        added = self.ctx.add_annotation.execute(
            AddAnnotationCommand(
                actor=self.ctx.treasurer, reference_no=self.donation.reference_no, text=leaked
            )
        )
        self.ctx.redact_annotation.execute(
            RedactAnnotationCommand(actor=self.ctx.admin, annotation_id=added.annotation_id)
        )
        ann = self.ctx.store.annotations[added.annotation_id]
        self.assertTrue(ann.is_redacted)
        self.assertEqual(ann.content, REDACTION_TOMBSTONE)
        self.assertIsNotNone(ann.redacted_by)
        # The leaked text must exist nowhere in the audit log.
        for entry in self.ctx.store.audit:
            self.assertNotIn(leaked, str(entry.summary))
        redactions = [e for e in self.ctx.store.audit if e.action == ANNOTATION_REDACTED]
        self.assertEqual(len(redactions), 1)

    def test_treasurer_cannot_redact(self) -> None:
        added = self.ctx.add_annotation.execute(
            AddAnnotationCommand(
                actor=self.ctx.treasurer, reference_no=self.donation.reference_no, text="oops name"
            )
        )
        with self.assertRaises(PermissionDeniedError):
            self.ctx.redact_annotation.execute(
                RedactAnnotationCommand(actor=self.ctx.treasurer, annotation_id=added.annotation_id)
            )

    def test_redact_unknown_annotation_raises(self) -> None:
        with self.assertRaises(AnnotationNotFoundError):
            self.ctx.redact_annotation.execute(
                RedactAnnotationCommand(actor=self.ctx.admin, annotation_id="nope")
            )


if __name__ == "__main__":
    unittest.main()
