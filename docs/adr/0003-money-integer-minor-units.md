# ADR-0003 — Money as Integer Minor Units (tiyin)

**Status:** Accepted — 2026-07-09

## Context
Money math with floating-point types introduces rounding errors that accumulate
and undermine trust in reports. The system handles UZS today and may handle other
currencies later. Reports and balances must be exact and reproducible.

## Decision
- Store every monetary amount as an **integer number of minor units (tiyin)**,
  where `1 UZS = 100 tiyin`, in a `BIGINT` column (`amount_minor`).
- **Never** use floating-point for money anywhere it is stored, computed, or
  transmitted internally.
- Wrap amounts in a `Money` value object (amount + currency) that forbids mixing
  currencies and centralizes all money arithmetic.
- Persist an explicit `currency` field (value `"UZS"` in v1) so multi-currency is
  additive later, with no migration of existing rows.
- Formatting (grouping, "so'm" suffix, locale) happens only in the presentation
  layer; the core always speaks integer minor units.

## Consequences
- ✅ Exact arithmetic; no rounding drift; reproducible balances and reports.
- ✅ Ready for multi-currency without reworking storage.
- ➖ Callers must convert to/from minor units at the boundary (a small, well-tested
  concern).
- Note: tiyin is effectively obsolete in everyday UZS use, but storing minor units
  (exponent 2) is the safe, standard approach and costs nothing.

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) §1.
