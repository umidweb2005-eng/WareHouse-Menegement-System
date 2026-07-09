"""Input parsing (framework-independent).

Parses a user-typed amount in so'm into a :class:`Money` of integer minor units.
Accepts spaces/underscores/commas as thousands separators. Rejects non-positive
or non-integer input (v1 is whole-so'm). No aiogram dependency.
"""

from __future__ import annotations

from donation_bot.domain.money import UZS, Currency, Money


class AmountParseError(ValueError):
    """Raised when a user-supplied amount cannot be parsed."""


def parse_amount_to_money(text: str, currency: Currency = UZS) -> Money:
    cleaned = text.strip().replace(" ", "").replace("_", "").replace(",", "")
    if not cleaned or not cleaned.isdigit():
        raise AmountParseError("amount must be a positive whole number of so'm")
    major = int(cleaned)
    if major <= 0:
        raise AmountParseError("amount must be greater than zero")
    return Money.from_major(major, currency)
