"""Access entities: roles, staff users, the system actor, and role presets.

Permission-based RBAC (see ``docs/USER_ROLES.md``): a role bundles permissions,
staff hold roles, and authorization resolves to the union of a user's role
permissions. Public/unregistered users are never persisted and receive
:data:`~donation_bot.domain.access.permissions.PUBLIC_PERMISSIONS` by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from donation_bot.domain.access.permissions import (
    PUBLIC_PERMISSIONS,
    SUPER_ADMIN_PERMISSIONS,
    TREASURER_PERMISSIONS,
    Permission,
)
from donation_bot.domain.errors import DomainError


@dataclass(frozen=True, slots=True)
class Role:
    code: str
    name: str
    permissions: frozenset[Permission]
    is_system: bool = False


@dataclass(frozen=True, slots=True)
class StaffUser:
    """A registered operator (Treasurer/Super Admin) or the reserved system actor.

    Donors/public users are never represented here. The system actor has no
    Telegram ID and no roles; it is authorized by execution context, not by
    permission checks (BR-SY / ADR-0011).
    """

    user_id: str
    telegram_id: int | None
    roles: frozenset[Role] = field(default_factory=frozenset)
    display_name: str | None = None
    is_system: bool = False
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.is_system and self.telegram_id is not None:
            raise DomainError("the system actor must not have a telegram_id")
        if not self.is_system and self.telegram_id is None:
            raise DomainError("a human staff user requires a telegram_id")
        if not self.user_id:
            raise DomainError("user_id is required")

    @property
    def effective_permissions(self) -> frozenset[Permission]:
        if not self.is_active:
            return frozenset()
        result: set[Permission] = set()
        for role in self.roles:
            result |= role.permissions
        return frozenset(result)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.effective_permissions


# ---------------------------------------------------------------------------
# Role presets (seeded at first run; "roles are data", these are the canonical v1
# defaults). See docs/USER_ROLES.md §2-3.
# ---------------------------------------------------------------------------
USER_ROLE = Role(
    code="user",
    name="User",
    permissions=PUBLIC_PERMISSIONS,
    is_system=True,
)
TREASURER_ROLE = Role(
    code="treasurer",
    name="Treasurer",
    permissions=TREASURER_PERMISSIONS,
    is_system=True,
)
SUPER_ADMIN_ROLE = Role(
    code="super_admin",
    name="Super Admin",
    permissions=SUPER_ADMIN_PERMISSIONS,
    is_system=True,
)

SYSTEM_ACTOR_USER_ID = "system"


def system_actor() -> StaffUser:
    """The reserved, non-login principal that authors machine-initiated records."""
    return StaffUser(
        user_id=SYSTEM_ACTOR_USER_ID,
        telegram_id=None,
        roles=frozenset(),
        display_name="System",
        is_system=True,
        is_active=True,
    )


def permissions_for(user: StaffUser | None) -> frozenset[Permission]:
    """Effective permissions for a caller; unregistered callers get public perms."""
    if user is None:
        return PUBLIC_PERMISSIONS
    return user.effective_permissions
