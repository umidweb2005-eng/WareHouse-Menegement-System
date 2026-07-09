"""Ledger entities: immutable donation/expense entries and reversals.

Invariants realized here (see ``docs/BUSINESS_RULES.md`` §2-4):

- An original entry's amount must be strictly positive (BR-M3).
- A donation carries a ``source`` and **no** free text; an expense carries a
  category and a required **public** usage description (BR-D2/BR-E2).
- A **reversal stores no amount of its own** — its effect is derived from the
  original it targets, so it can never cancel a different amount (BR-L3).
- A reversal cannot target another reversal: only :class:`LedgerEntry` (an
  original) exposes ``reverse()``; :class:`Reversal` does not — enforced by type.

Entities are frozen. Persistence assigns ``entry_id``, ``reference_no`` and
``recorded_at``; the domain treats them as optional until then.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from donation_bot.domain.errors import InvalidLedgerEntryError, ReversalError
from donation_bot.domain.money import UZS, Currency, Money


class EntryKind(str, Enum):
    DONATION = "donation"
    EXPENSE = "expense"


class EntryRole(str, Enum):
    ORIGINAL = "original"
    REVERSAL = "reversal"


class DonationSource(str, Enum):
    CASH = "cash"
    BANK_MANUAL = "bank_manual"
    BANK_API = "bank_api"


def _require_aware(moment: datetime, field: str) -> None:
    if moment.tzinfo is None:
        raise InvalidLedgerEntryError(f"{field} must be timezone-aware (UTC)")


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """An original financial fact: a donation received or an expense paid."""

    kind: EntryKind
    amount: Money
    event_at: datetime
    recorded_by: str
    source: DonationSource | None = None
    expense_category_id: int | None = None
    expense_description: str | None = None
    entry_id: str | None = None
    reference_no: int | None = None
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.amount.is_positive:
            raise InvalidLedgerEntryError("entry amount must be strictly positive")
        _require_aware(self.event_at, "event_at")
        if not self.recorded_by:
            raise InvalidLedgerEntryError("recorded_by is required")

        if self.kind is EntryKind.DONATION:
            if self.source is None:
                raise InvalidLedgerEntryError("donation requires a source")
            if self.expense_category_id is not None or self.expense_description is not None:
                raise InvalidLedgerEntryError("donation must not carry expense fields")
        elif self.kind is EntryKind.EXPENSE:
            if self.expense_category_id is None:
                raise InvalidLedgerEntryError("expense requires a category")
            if not (self.expense_description and self.expense_description.strip()):
                raise InvalidLedgerEntryError("expense requires a public usage description")
            if self.source is not None:
                raise InvalidLedgerEntryError("expense must not carry a donation source")
        else:  # pragma: no cover - Enum guards this
            raise InvalidLedgerEntryError(f"unknown entry kind: {self.kind!r}")

    @property
    def entry_role(self) -> EntryRole:
        return EntryRole.ORIGINAL

    @property
    def currency(self) -> Currency:
        return self.amount.currency

    @property
    def signed_effective_amount(self) -> Money:
        """+amount for a donation (inflow), -amount for an expense (outflow)."""
        return self.amount if self.kind is EntryKind.DONATION else -self.amount

    def reverse(self, *, reason: str, recorded_by: str) -> Reversal:
        """Create a reversal of this entry. Amount is derived, not supplied."""
        return Reversal(original=self, reason=reason, recorded_by=recorded_by)


@dataclass(frozen=True, slots=True)
class Reversal:
    """A correction that cancels exactly one original entry.

    It holds **no** amount, currency, kind, or event time of its own; every such
    value is derived from :attr:`original`. This makes it structurally impossible
    for a reversal to cancel a different amount than the entry it targets.
    """

    original: LedgerEntry
    reason: str
    recorded_by: str
    entry_id: str | None = None
    reference_no: int | None = None
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.original, LedgerEntry):
            raise ReversalError("a reversal can only target an original ledger entry")
        if self.original.entry_role is not EntryRole.ORIGINAL:  # pragma: no cover
            raise ReversalError("cannot reverse a reversal")
        if not (self.reason and self.reason.strip()):
            raise ReversalError("a reversal requires a non-empty reason")
        if not self.recorded_by:
            raise ReversalError("recorded_by is required")

    @property
    def entry_role(self) -> EntryRole:
        return EntryRole.REVERSAL

    @property
    def kind(self) -> EntryKind:
        return self.original.kind

    @property
    def amount(self) -> Money:
        return self.original.amount

    @property
    def event_at(self) -> datetime:
        return self.original.event_at

    @property
    def signed_effective_amount(self) -> Money:
        """The negation of the target's effect, so a reversed pair nets to zero."""
        return -self.original.signed_effective_amount


AnyEntry = LedgerEntry | Reversal


# ---------------------------------------------------------------------------
# Factory helpers (ergonomic, validated construction)
# ---------------------------------------------------------------------------
def record_donation(
    *,
    amount: Money,
    source: DonationSource,
    event_at: datetime,
    recorded_by: str,
    entry_id: str | None = None,
    reference_no: int | None = None,
    recorded_at: datetime | None = None,
) -> LedgerEntry:
    return LedgerEntry(
        kind=EntryKind.DONATION,
        amount=amount,
        event_at=event_at,
        recorded_by=recorded_by,
        source=source,
        entry_id=entry_id,
        reference_no=reference_no,
        recorded_at=recorded_at,
    )


def record_expense(
    *,
    amount: Money,
    category_id: int,
    description: str,
    event_at: datetime,
    recorded_by: str,
    entry_id: str | None = None,
    reference_no: int | None = None,
    recorded_at: datetime | None = None,
) -> LedgerEntry:
    return LedgerEntry(
        kind=EntryKind.EXPENSE,
        amount=amount,
        event_at=event_at,
        recorded_by=recorded_by,
        expense_category_id=category_id,
        expense_description=description,
        entry_id=entry_id,
        reference_no=reference_no,
        recorded_at=recorded_at,
    )


# ---------------------------------------------------------------------------
# Derived read helpers
# ---------------------------------------------------------------------------
def balance(entries: Iterable[AnyEntry], currency: Currency = UZS) -> Money:
    """Net balance = sum of signed effective amounts. Reversed pairs net to zero."""
    total = Money.zero(currency)
    for entry in entries:
        total = total + entry.signed_effective_amount
    return total


def is_reversed(entry: LedgerEntry, reversals: Iterable[Reversal]) -> bool:
    """Whether any reversal targets ``entry`` (derived state, never stored)."""
    for reversal in reversals:
        target = reversal.original
        if entry.entry_id is not None and target.entry_id is not None:
            if entry.entry_id == target.entry_id:
                return True
        elif target is entry:
            return True
    return False
