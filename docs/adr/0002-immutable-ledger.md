# ADR-0002 — Immutable, Append-Only Ledger with Reversal-Only Corrections

**Status:** Accepted — 2026-07-09

## Context
Transparency is a core goal. If a treasurer (or anyone, including a Super Admin)
could silently edit or delete a past donation or expense, reported totals could
not be trusted and "transparency" would be meaningless. Financial systems solve
this with append-only ledgers and reversing entries.

## Decision
- Donations and expenses are stored as **append-only ledger entries**; financial
  fields are **never updated** and rows are **never deleted** — by any role.
- Corrections are made only by posting an **adjustment (reversal) entry** that
  references the original; if a corrected value is needed, a fresh correct entry
  is posted afterward.
- Each entry can be reversed **at most once** (`UNIQUE(reverses_entry_id)`);
  reversals cannot themselves be reversed; every reversal carries a required
  reason and is audited.
- "Reversed" is a **derived** state (a reversal exists that references the entry),
  never a mutable flag on the original.
- Defense in depth: append-only DB triggers reject `UPDATE`/`DELETE`, and the
  application connects with a DB role lacking those privileges.

Store donations and expenses in **one** `ledger_entries` table (distinguished by
`entry_kind` and `entry_role`) because they share identical lifecycle rules; this
keeps reversal logic and balance computation in one place.

## Consequences
- ✅ History is trustworthy and reproducible; reports can always be recomputed.
- ✅ Full audit trail; restores are coherent (no destructive edits between backups).
- ➖ "Fixing a typo" requires a reversal + re-entry, which is more steps than an
  edit — an intentional trade for integrity.
- ➖ Balance is a computed sum, not a stored number (see ADR-0007).

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) and
[`DATABASE_DESIGN.md`](../DATABASE_DESIGN.md).

## Amendment (2026-07-09, Phase 2.5 review)
Two refinements, captured in later ADRs (this decision stands):
- A reversal now stores **no amount/kind/currency/event-time of its own**; its
  effect is **derived** from the target, so it cannot cancel a different amount.
  See [ADR-0010](./0010-annotations-and-derived-reversal.md).
- The "restores are coherent" consequence assumed restore is benign. The review
  recognized restore as a tamper vector and moved it to an operator-only,
  off-box-audited procedure. See [ADR-0008](./0008-backup-restore-anti-tamper.md).
