"""Money value-object tests (invariant I4: integer minor units, exact math)."""

from __future__ import annotations

import unittest

from donation_bot.domain.errors import CurrencyMismatchError, InvalidMoneyError
from donation_bot.domain.money import UZS, Currency, Money


class MoneyConstructionTests(unittest.TestCase):
    def test_from_major_converts_to_minor_units(self) -> None:
        self.assertEqual(Money.from_major(5000).amount_minor, 500000)  # 5000 so'm

    def test_rejects_float_amount(self) -> None:
        with self.assertRaises(InvalidMoneyError):
            Money(1000.0)  # type: ignore[arg-type]

    def test_rejects_bool_amount(self) -> None:
        with self.assertRaises(InvalidMoneyError):
            Money(True)  # type: ignore[arg-type]

    def test_zero_and_sign_predicates(self) -> None:
        self.assertTrue(Money.zero().is_zero)
        self.assertTrue(Money(1).is_positive)
        self.assertTrue(Money(-1).is_negative)

    def test_invalid_currency_code(self) -> None:
        for bad in ("us", "usdd", "uz1", "usd"):
            with self.assertRaises(InvalidMoneyError):
                Currency(bad, 2)


class MoneyArithmeticTests(unittest.TestCase):
    def test_add_and_sub_same_currency(self) -> None:
        self.assertEqual((Money(300) + Money(200)).amount_minor, 500)
        self.assertEqual((Money(300) - Money(500)).amount_minor, -200)

    def test_negation(self) -> None:
        self.assertEqual((-Money(700)).amount_minor, -700)

    def test_currency_mismatch_is_rejected(self) -> None:
        eur = Currency("EUR", 2)
        with self.assertRaises(CurrencyMismatchError):
            Money(100, UZS) + Money(100, eur)
        with self.assertRaises(CurrencyMismatchError):
            _ = Money(100, UZS) < Money(100, eur)

    def test_comparisons(self) -> None:
        self.assertLess(Money(100), Money(200))
        self.assertGreaterEqual(Money(200), Money(200))


if __name__ == "__main__":
    unittest.main()
