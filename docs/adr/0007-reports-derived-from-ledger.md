# ADR-0007 — Reports Derived from the Ledger

**Status:** Accepted — 2026-07-09

## Context
Transparency requires that any figure the community sees can be independently
reproduced. If totals were typed in or stored as editable numbers, they could
drift from reality or be manipulated, defeating the purpose. The system already
commits to an immutable ledger (ADR-0002).

## Decision
- **Every reported figure is derived from the ledger** at query time (or from a
  materialized view that is itself computed from the ledger). No total is ever
  hand-entered or stored as an editable number.
- Balance = sum of effective (signed) amounts over ledger entries; reversed pairs
  net to zero.
- Reports support day / month / year / all-time (and custom ranges), bucketed in
  the **organization time zone** (`Asia/Tashkent` by default); timestamps are
  stored in UTC and converted for reporting.
- Given the same ledger state and period, a report always yields identical
  numbers (reproducibility). Corrections affect future output only by adding new
  entries — never by altering historical rows.

## Consequences
- ✅ Numbers are always verifiable and reproducible; trust by construction.
- ✅ No "stored total" to keep in sync or to tamper with.
- ➖ Heavy reporting could become expensive at large scale; mitigated later with
  materialized views / pre-aggregation that remain **derived** from the ledger
  (an optimization, not a change of source of truth).
- ➖ Correct time-zone bucketing must be tested carefully (midnight boundaries).

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) §5 and
[`TESTING_STRATEGY.md`](../TESTING_STRATEGY.md) §3.3.
