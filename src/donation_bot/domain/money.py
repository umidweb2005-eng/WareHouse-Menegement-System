"""Money value object — integer minor units only, never floats.

All amounts are stored and computed as an integer number of **minor units**
(tiyin for UZS, where 1 UZS = 100 tiyin). Floating-point money is forbidden
(see ``docs/BUSINESS_RULES.md`` §1 and ``docs/adr/0003-money-integer-minor-units.md``).

``Money`` may hold any integer, including zero or negative values, because it is
also the result type of aggregations such as a balance. The rule that *recorded*
donation/expense amounts must be strictly positive is enforced by the ledger
entities, not by ``Money`` itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from donation_bot.domain.errors import CurrencyMismatchError, InvalidMoneyError


@dataclass(frozen=True, slots=True)
class Currency:
    """A currency with its minor-unit exponent (UZS -> exponent 2, i.e. tiyin)."""

    code: str
    exponent: int

    def __post_init__(self) -> None:
        if len(self.code) != 3 or not self.code.isalpha() or not self.code.isupper():
            raise InvalidMoneyError(f"currency code must be 3 uppercase letters, got {self.code!r}")
        if self.exponent < 0:
            raise InvalidMoneyError("currency exponent must be non-negative")

    @property
    def minor_per_major(self) -> int:
        return 10**self.exponent


# The single v1 currency. Multi-currency is a future extension; the currency is
# carried explicitly on Money so nothing needs re-storing later.
UZS = Currency("UZS", 2)


@dataclass(frozen=True, slots=True)
class Money:
    """An exact monetary amount as integer minor units plus its currency."""

    amount_minor: int
    currency: Currency = UZS

    def __post_init__(self) -> None:
        # ``bool`` is an ``int`` subclass; exclude it. Reject floats explicitly.
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise InvalidMoneyError(
                f"amount_minor must be an int (minor units), got {type(self.amount_minor).__name__}"
            )

    # -- constructors --------------------------------------------------------
    @classmethod
    def zero(cls, currency: Currency = UZS) -> Money:
        return cls(0, currency)

    @classmethod
    def from_major(cls, major: int, currency: Currency = UZS) -> Money:
        """Build from whole major units (e.g., 5000 so'm -> 500000 tiyin)."""
        if isinstance(major, bool) or not isinstance(major, int):
            raise InvalidMoneyError("major units must be an int")
        return cls(major * currency.minor_per_major, currency)

    # -- predicates ----------------------------------------------------------
    @property
    def is_positive(self) -> bool:
        return self.amount_minor > 0

    @property
    def is_zero(self) -> bool:
        return self.amount_minor == 0

    @property
    def is_negative(self) -> bool:
        return self.amount_minor < 0

    # -- arithmetic (same-currency only) ------------------------------------
    def _check_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"cannot combine {self.currency.code} and {other.currency.code}"
            )

    def __add__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount_minor, self.currency)

    # -- comparisons (same-currency only) -----------------------------------
    def __lt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount_minor < other.amount_minor

    def __le__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount_minor <= other.amount_minor

    def __gt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount_minor > other.amount_minor

    def __ge__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount_minor >= other.amount_minor

    def __repr__(self) -> str:
        return f"Money(amount_minor={self.amount_minor}, currency={self.currency.code})"
