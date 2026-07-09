# ADR-0009 — Public/Private Data Split & the PII-Erasure Exception

**Status:** Accepted — 2026-07-09 (from Phase 2.5 review)

## Context
Privacy is the highest principle, yet the system also promises transparency and an
append-only ledger. The Phase 2.5 review surfaced two problems: (1) it was
undefined which free text was public vs private, and donation "notes" were an
unmanaged donor-identity channel; (2) "append-only everything" left **no way to
remove donor identity a human accidentally typed into free text**, even though
privacy is supposed to outrank immutability.

## Decision
**A first-class public/private split:**
- **Public:** reports, statistics, balance, the donation account, and expense
  **usage descriptions**.
- **Private (staff-only):** annotations, reversal reasons, audit logs, staff
  identities.
- Donations carry **no public free text**, so donor identity cannot reach a public
  surface. Expense descriptions concern spending (vendors/purpose), not donors.

**A narrow PII-erasure exception:**
- A Super Admin with `pii.erase` may **redact** the free-text content of an
  annotation or reversal reason, solely to remove leaked donor identity.
- Redaction **overwrites** the text with a tombstone (genuinely removed, not
  hidden), touches **only** free text (never financial fields), and is **audited
  without copying** the leaked text.
- This is the single, deliberate exception to append-only content.

## Consequences
- ✅ No public surface can leak donor identity (structural).
- ✅ Privacy can always win, even after human error, without weakening financial
  immutability.
- ✅ Audit never becomes a second copy of leaked PII.
- ➖ One table (`entry_annotations`) is "controlled-mutable" rather than strictly
  append-only — a deliberate, well-scoped carve-out captured in the mutability
  matrix.

See [`BUSINESS_RULES.md`](../BUSINESS_RULES.md) §7–8, [`SECURITY.md`](../SECURITY.md) §2–3.
