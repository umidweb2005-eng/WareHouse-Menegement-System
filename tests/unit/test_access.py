"""Access/RBAC tests (authorization by permission, system actor, presets)."""

from __future__ import annotations

import unittest

from donation_bot.domain.access.entities import (
    SUPER_ADMIN_ROLE,
    TREASURER_ROLE,
    USER_ROLE,
    StaffUser,
    permissions_for,
    system_actor,
)
from donation_bot.domain.access.permissions import PUBLIC_PERMISSIONS, Permission
from donation_bot.domain.errors import DomainError


class RolePresetTests(unittest.TestCase):
    def test_user_role_is_public_permissions(self) -> None:
        self.assertEqual(USER_ROLE.permissions, PUBLIC_PERMISSIONS)

    def test_treasurer_can_record_but_not_govern(self) -> None:
        self.assertIn(Permission.DONATION_RECORD, TREASURER_ROLE.permissions)
        self.assertIn(Permission.ENTRY_ANNOTATE, TREASURER_ROLE.permissions)
        self.assertNotIn(Permission.USER_MANAGE, TREASURER_ROLE.permissions)
        self.assertNotIn(Permission.PII_ERASE, TREASURER_ROLE.permissions)

    def test_super_admin_holds_every_permission(self) -> None:
        self.assertEqual(SUPER_ADMIN_ROLE.permissions, frozenset(Permission))
        for p in (Permission.PII_ERASE, Permission.BACKUP_MANAGE, Permission.AUDIT_VIEW):
            self.assertIn(p, SUPER_ADMIN_ROLE.permissions)


class StaffUserTests(unittest.TestCase):
    def test_effective_permissions_are_union_of_roles(self) -> None:
        user = StaffUser(user_id="u1", telegram_id=111, roles=frozenset({TREASURER_ROLE}))
        self.assertTrue(user.has_permission(Permission.EXPENSE_RECORD))
        self.assertFalse(user.has_permission(Permission.SETTINGS_MANAGE))

    def test_inactive_user_has_no_permissions(self) -> None:
        user = StaffUser(
            user_id="u1", telegram_id=111, roles=frozenset({SUPER_ADMIN_ROLE}), is_active=False
        )
        self.assertEqual(user.effective_permissions, frozenset())
        self.assertFalse(user.has_permission(Permission.AUDIT_VIEW))

    def test_human_requires_telegram_id(self) -> None:
        with self.assertRaises(DomainError):
            StaffUser(user_id="u1", telegram_id=None)

    def test_permissions_for_unregistered_is_public_set(self) -> None:
        self.assertEqual(permissions_for(None), PUBLIC_PERMISSIONS)


class SystemActorTests(unittest.TestCase):
    def test_system_actor_has_no_telegram_id_and_no_permissions(self) -> None:
        actor = system_actor()
        self.assertTrue(actor.is_system)
        self.assertIsNone(actor.telegram_id)
        # Authorized by context, not RBAC: it holds no permissions.
        self.assertEqual(actor.effective_permissions, frozenset())
        self.assertFalse(actor.has_permission(Permission.BACKUP_MANAGE))

    def test_system_actor_must_not_have_telegram_id(self) -> None:
        with self.assertRaises(DomainError):
            StaffUser(user_id="system", telegram_id=555, is_system=True)


if __name__ == "__main__":
    unittest.main()
