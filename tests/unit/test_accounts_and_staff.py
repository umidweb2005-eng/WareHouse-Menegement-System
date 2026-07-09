"""Tests for donation account, staff registration, identity, and bootstrap seed."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import _appsupport as app

from donation_bot.application.access.identity import resolve_actor
from donation_bot.application.access.register_staff import RegisterStaffCommand
from donation_bot.application.bootstrap import ensure_seed
from donation_bot.application.errors import PermissionDeniedError, StaffAlreadyRegisteredError
from donation_bot.application.settings.configure_account import ConfigureDonationAccountCommand
from donation_bot.domain.accounts.entities import AccountType, DonationAccount
from donation_bot.domain.access.entities import (
    SYSTEM_ACTOR_USER_ID,
    TREASURER_ROLE,
    system_actor,
)
from donation_bot.domain.errors import DomainError

UTC = timezone.utc
NOW = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


class DonationAccountEntityTests(unittest.TestCase):
    def test_active_account_requires_value(self) -> None:
        with self.assertRaises(DomainError):
            DonationAccount(
                label="Card", account_type=AccountType.CARD, created_by="a", created_at=NOW
            )

    def test_disabled_account_has_no_value(self) -> None:
        acc = DonationAccount(
            label="Off", account_type=AccountType.DISABLED, created_by="a", created_at=NOW
        )
        self.assertTrue(acc.is_disabled)


class RegisterStaffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_admin_registers_treasurer(self) -> None:
        result = self.ctx.register_staff.execute(
            RegisterStaffCommand(
                actor=self.ctx.admin, telegram_id=5555, role=TREASURER_ROLE, display_name="New T"
            )
        )
        staff = self.ctx.staff_repo.get(result.user_id)
        self.assertIsNotNone(staff)
        self.assertEqual(staff.telegram_id, 5555)
        self.assertIn(TREASURER_ROLE, staff.roles)

    def test_duplicate_telegram_id_rejected(self) -> None:
        self.ctx.register_staff.execute(
            RegisterStaffCommand(actor=self.ctx.admin, telegram_id=5555, role=TREASURER_ROLE)
        )
        with self.assertRaises(StaffAlreadyRegisteredError):
            self.ctx.register_staff.execute(
                RegisterStaffCommand(actor=self.ctx.admin, telegram_id=5555, role=TREASURER_ROLE)
            )

    def test_treasurer_cannot_register_staff(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.register_staff.execute(
                RegisterStaffCommand(
                    actor=self.ctx.treasurer, telegram_id=6666, role=TREASURER_ROLE
                )
            )


class DonationAccountUseCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = app.build()

    def test_configure_then_read_active(self) -> None:
        self.assertIsNone(self.ctx.get_active_account.execute(actor=None))
        self.ctx.configure_account.execute(
            ConfigureDonationAccountCommand(
                actor=self.ctx.admin,
                label="Main card",
                account_type=AccountType.CARD,
                account_value="8600 1234 5678 9012",
                holder_name="Masjid",
            )
        )
        active = self.ctx.get_active_account.execute(actor=None)  # public read
        self.assertIsNotNone(active)
        self.assertEqual(active.account_value, "8600 1234 5678 9012")

    def test_latest_account_is_active(self) -> None:
        for value in ("1111", "2222"):
            self.ctx.configure_account.execute(
                ConfigureDonationAccountCommand(
                    actor=self.ctx.admin,
                    label="Card",
                    account_type=AccountType.CARD,
                    account_value=value,
                )
            )
        self.assertEqual(self.ctx.get_active_account.execute().account_value, "2222")

    def test_non_admin_cannot_configure(self) -> None:
        with self.assertRaises(PermissionDeniedError):
            self.ctx.configure_account.execute(
                ConfigureDonationAccountCommand(
                    actor=self.ctx.treasurer,
                    label="x",
                    account_type=AccountType.CARD,
                    account_value="1",
                )
            )


class IdentityTests(unittest.TestCase):
    def test_resolve_known_and_unknown(self) -> None:
        ctx = app.build()
        ctx.staff_repo.add(ctx.treasurer)
        self.assertEqual(resolve_actor(ctx.staff_repo, ctx.treasurer.telegram_id), ctx.treasurer)
        self.assertIsNone(resolve_actor(ctx.staff_repo, 99999))  # public

    def test_system_actor_never_resolves_as_caller(self) -> None:
        ctx = app.build()
        ctx.staff_repo.add(system_actor())
        # system actor has no telegram_id, so it can't be a caller anyway;
        # ensure it is excluded from active listing too.
        self.assertEqual(ctx.staff_repo.list_active(), ())


class BootstrapSeedTests(unittest.TestCase):
    def test_seed_is_idempotent_and_creates_admin_and_system_actor(self) -> None:
        ctx = app.build()

        def seed() -> None:
            ensure_seed(
                ctx.uow_factory,
                ctx.clock,
                ctx.ids,
                first_super_admin_telegram_id=42,
                first_super_admin_name="Boss",
            )

        seed()
        seed()  # second call must not duplicate

        admin = ctx.staff_repo.get_by_telegram_id(42)
        self.assertIsNotNone(admin)
        self.assertIsNotNone(ctx.staff_repo.get(SYSTEM_ACTOR_USER_ID))
        # exactly one active (human) staff member
        self.assertEqual(len(ctx.staff_repo.list_active()), 1)


if __name__ == "__main__":
    unittest.main()
