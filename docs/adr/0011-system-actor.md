# ADR-0011 — System Actor for Machine-Initiated Actions

**Status:** Accepted — 2026-07-09 (from Phase 2.5 review)

## Context
`ledger_entries.recorded_by` and `audit_logs.actor_user_id` need a defined author.
Some records are not created by a human: the scheduled backup job today, and
automatic bank/payment imports later (BR-D5). The original schema made
`recorded_by` a non-null FK to a human staff row, which the future automatic path
would violate — a painful retrofit on the most sensitive table if left to later.

## Decision
- Introduce one reserved **system actor**: a `staff_users` row with
  `is_system = true` and a **NULL `telegram_id`** (it cannot log in), seeded at
  first run.
- Machine-initiated writes (scheduled jobs; future auto-imports) are **authored by
  the system actor** and go through the same use cases, producing the same audit
  trail; they are authorized by execution context, not a human permission check
  (BR-SY).
- The system actor is never assigned to a person and holds no interactive role.

## Consequences
- ✅ Every ledger/audit row has a defined, non-null author, human or machine.
- ✅ The future bank-integration path (ADR references in
  [`API_INTEGRATIONS.md`](../API_INTEGRATIONS.md)) needs **no schema change** to
  `ledger_entries`.
- ✅ Only trivial v1 use (the scheduled backup job); cost now is one seed row.
- ➖ Code must guard that the system actor can never be used as a login/human
  principal (covered by a test).

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) §9 and
[`DATABASE_DESIGN.md`](../DATABASE_DESIGN.md) §4.
