# ADR-0010 — Annotations for Context & Derived Reversal Amounts

**Status:** Accepted — 2026-07-09 (from Phase 2.5 review)

## Context
Two Phase 2.5 findings:
1. The bot offered "add a note later," but a note lived on the immutable ledger
   row — adding/editing it would be an `UPDATE` on an append-only table
   (contradiction).
2. A reversal stored its **own** amount; a buggy or malicious insert could create
   a reversal that cancels a *different* amount than its target, corrupting the
   balance while looking legitimate.

## Decision
**Annotations instead of editing entries.**
- The immutable `ledger_entries` row holds only structured financial facts plus
  the **public** expense usage description.
- All optional staff free text (context **notes** and required **reversal
  reasons**) lives in a separate append-only `entry_annotations` table, added by
  *insert*. Adding context after recording never mutates the entry.
- Annotations are private and PII-redactable (ADR-0009).

**Reversal amount is derived, not stored.**
- A reversal row stores no amount/currency/kind/event-time of its own; its effect
  is **derived from the original** it references (via the `ledger_effective`
  view). It is structurally impossible for a reversal to cancel a different
  amount.
- One reversal per entry (`UNIQUE(reverses_entry_id)`); a reversal cannot target
  another reversal.

## Consequences
- ✅ Adding context is always an append — no contradiction with immutability.
- ✅ An entire class of balance-corruption bug/tamper is eliminated by design.
- ✅ Balance = Σ signed effective amounts; reversed pairs net to zero
  automatically.
- ➖ Reads for reversals require a join to the target (handled once in the
  `ledger_effective` view).

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) §2, §6 and
[`DATABASE_DESIGN.md`](../DATABASE_DESIGN.md) §5. Refines ADR-0002.
