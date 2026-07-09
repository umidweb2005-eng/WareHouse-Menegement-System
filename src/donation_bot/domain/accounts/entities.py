"""Donation account entity: the public destination donors send money to.

Append-only history — a change is a new row, and the **active** account is the
most recently created one (see ``docs/DATABASE_DESIGN.md`` §6). It is *not* a
donor's account and contains no donor data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from donation_bot.domain.errors import DomainError


class AccountType(str, Enum):
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    WALLET = "wallet"
    DISABLED = "disabled"  # donations temporarily not accepted


@dataclass(frozen=True, slots=True)
class DonationAccount:
    label: str
    account_type: AccountType
    created_by: str
    created_at: datetime
    account_value: str | None = None  # None only when disabled
    holder_name: str | None = None
    account_id: str | None = None

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise DomainError("donation account requires a label")
        if self.created_at.tzinfo is None:
            raise DomainError("created_at must be timezone-aware (UTC)")
        if self.account_type is AccountType.DISABLED:
            if self.account_value is not None:
                raise DomainError("a disabled account must not carry an account_value")
        elif not (self.account_value and self.account_value.strip()):
            raise DomainError("an active account requires an account_value")

    @property
    def is_disabled(self) -> bool:
        return self.account_type is AccountType.DISABLED
