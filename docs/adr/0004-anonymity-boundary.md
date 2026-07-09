# ADR-0004 — Structural Donor-Anonymity Boundary

**Status:** Accepted — 2026-07-09

## Context
Donor anonymity is the project's highest principle. Telegram unavoidably delivers
the sender's ID to the bot on every update, yet the system must **never persist**
donor identity. At the same time, treasurers and Super Admins must be identified
for authorization and audit. Relying on "remember to be careful" is not enough for
a multi-year system.

## Decision
Make anonymity a **structural guarantee**, not a policy:
- **Two identity tiers.** Public/donor identities are used transiently to reply
  and then discarded (never stored, never logged). **Staff** (Treasurer, Super
  Admin) Telegram IDs are stored because authorization and audit require them.
- **No capability to store donor identity.** No donation-related table has any
  donor identity column, and the `RecordDonation` command has no field for it —
  there is nowhere to put donor identity.
- **Donations are recorded by treasurers**, not donors, so no donor session or
  contact is ever involved.
- **Receipts default to sensitive** and are never public, mitigating identity
  leakage via images (e.g., bank slips).
- **Future integrations must strip donor-identifying fields** from provider
  payloads before persistence.
- **Guard tests** assert that no donor-identity column/field can reappear via a
  future migration or code change.

## Consequences
- ✅ Even a full database breach cannot reveal who donated — the data was never
  captured.
- ✅ Storing staff IDs does not weaken donor anonymity (staff ≠ donors).
- ➖ Residual human-error risk (a treasurer typing a name into a free-text note);
  mitigated by UI warnings and treated-as-sensitive display; possible future PII
  scanning.
- ➖ Some convenience features that would require donor identity are permanently
  out of scope.

See [`SECURITY.md`](../SECURITY.md) and [`USER_ROLES.md`](../USER_ROLES.md).

## Amendment (2026-07-09, Phase 2.5 review)
This decision stands; two refinements:
- **Receipts moved to Version 2**, so the "receipts default to sensitive" mitigation
  is a V2 concern, not a v1 leak vector. In v1, donations carry **no** public free
  text, and donor-context notes live only in **private annotations**.
- The residual "human types a name into free text" risk is now backed by a concrete
  remedy — the audited **PII-erasure** exception — not just UI warnings. See
  [ADR-0009](./0009-public-private-and-pii-erasure.md).
