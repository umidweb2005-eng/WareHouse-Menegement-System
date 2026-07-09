# Glossary

> A shared, precise vocabulary. Every other document uses these terms with
> exactly these meanings. When in doubt, this file wins.
> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)

---

### Organization
The single entity whose funds are being managed. Version 1 supports exactly one
organization.

### Donation Account
The publicly shown destination for donations — for example a bank card number,
bank account, or wallet identifier that donors send money to. Configured by a
Super Admin and visible to everyone. It is **not** a donor's account.

### Donor
A person who gives money. Donors are **anonymous**. The system holds **no**
identifying information about them and no record ever references them.

### Public User (or "User")
Anyone interacting with the bot who is not a registered staff member. They can
view reports, statistics, and the donation account. They are **never persisted**.
The "User" role is the *implicit default* permission set applied to any
unregistered chat.

### Treasurer
A registered, trusted staff member authorized to record donations and expenses,
write public expense usage descriptions, and add optional private annotations.
Identity is stored for authorization and audit.

### Super Admin
A registered staff member with full governance authority: roles, permissions,
settings, donation account, audit logs, and backups; and the only role that may
perform the narrow, audited PII-erasure action.

### Staff
Collective term for registered users (Treasurers and Super Admins). Only staff
identities are persisted.

### System Actor
A reserved, non-login principal that owns records created by the machine rather
than by a person — scheduled jobs and (future) automatic bank/payment imports.
It gives every automated record a defined, audited author without a human
recorder. It cannot log in or use the bot.

---

### Ledger
The append-only collection of all financial facts (donations and expenses). The
ledger is the **single source of truth** for every reported number.

### Ledger Entry
A single **immutable** financial fact in the ledger. Its financial fields are
never updated and the row is never deleted, by anyone.

### Reference Number
A human-friendly, sequential public identifier assigned to every ledger entry
(e.g., `#1042`). Used so treasurers can select an entry to reverse and so entries
can be referred to unambiguously. Distinct from the internal UUID primary key.

### Donation (Inflow)
A ledger entry representing money **received** by the organization. Positive
amount. Contains no donor reference and no public free text.

### Expense / Expenditure (Outflow)
A ledger entry representing money **spent** by the organization. Carries a
**public usage description** so the community can see how donations were used.

### Adjustment Entry (Reversal)
The **only** way to correct a mistake. Instead of editing or deleting an existing
entry, a new entry is created that reverses the original; if a corrected value is
needed, a fresh correct entry is posted afterward. The original entry remains
forever. A reversal's amount and direction are **derived from the original** — it
cannot introduce a different amount. Every reversal carries a required reason and
is audited.

### Reversed Entry
An original entry that has had a reversal posted against it. Its "reversed" state
is **derived** (by the presence of a reversal that references it), not by
mutating the original row.

### Annotation
An optional, **private (staff-only)**, append-only note attached to any ledger
entry to record context (e.g., "Friday collection box"). Annotations — not the
immutable entry row — are how staff add information *after* an entry is recorded.
An annotation's text may be **redacted** (see below) but the entry itself is never
edited.

### Redaction (PII-erasure)
The narrow, audited action by which a Super Admin overwrites the free-text content
of an annotation (or reversal reason) **solely** to remove donor identity a human
entered by mistake. It genuinely removes the text (leaving a tombstone marker),
because privacy outranks immutability. It is the *only* permitted content
mutation, and it never touches financial fields.

### Balance
The current amount of money the organization holds, computed as
`SUM(active donations) − SUM(active expenses)` over the ledger. Always derived,
never stored as an editable figure.

### Minor Units (tiyin)
The integer unit in which all money is stored. `1 UZS = 100 tiyin`. Storing
integers (never floats) eliminates rounding error. Example: 5 000 UZS is stored
as `500000`. See [`BUSINESS_RULES.md`](./BUSINESS_RULES.md).

### Source
Where a donation record came from: `cash`, `bank_manual` (a bank transfer a
treasurer recorded by hand), or `bank_api` (future automatic import). Lets v1 and
future automation coexist in one ledger.

### External Transaction
A raw, imported record from a future payment provider or bank API, kept separate
from the domain ledger and linked via reconciliation. Enables idempotent imports.
**Future (post-v1).**

### Reconciliation
The process of matching an external transaction to a domain donation so nothing
is counted twice. **Future (post-v1).**

---

### Public vs Private information
A first-class distinction in this system:
- **Public:** reports, statistics, the donation account, and expense **usage
  descriptions** — visible to every bot user.
- **Private (staff-only):** annotations, reversal reasons, audit logs, and staff
  identities — never shown to public users.
Donations carry **no** public free text, so donor identity cannot leak through a
public field.

### Receipt / Attachment
An optional supporting file (image/PDF) for an entry. **Deferred to Version 2.**
Not part of v1 (this removes file-based donor-identity leakage risk from the first
release). When introduced, receipts default to sensitive and are access-controlled.

### Audit Log
An append-only record of every privileged action (who did what, when, and why).
Used for accountability; contains staff identities only, never donor identities.

---

### RBAC (Role-Based Access Control)
Authorization model where **permissions** are grouped into **roles**, and roles
are assigned to staff. See [`USER_ROLES.md`](./USER_ROLES.md).

### Permission
A single, fine-grained capability (e.g., `donation.record`, `report.view`,
`audit.view`). The unit that authorization checks are written against.

### Role
A named preset bundle of permissions (User, Treasurer, Super Admin). New roles
can be added without code changes.

---

### Hexagonal Architecture (Ports & Adapters)
An architectural style where the business core defines **ports** (interfaces) and
the outside world connects through **adapters** (Telegram, database, and future
bank APIs). See [`PROJECT_ARCHITECTURE.md`](./PROJECT_ARCHITECTURE.md).

### Port
An interface defined by the core describing something it needs (e.g., a
`LedgerRepository`) or something it offers (a use case).

### Adapter
A concrete implementation of a port for a specific technology (e.g., a
SQLAlchemy repository, an aiogram handler).

### Use Case (Application Service)
A single business operation orchestrated by the application layer (e.g.,
"Record a donation", "Reverse an entry", "Generate a monthly report").

### Domain
The innermost layer: entities, value objects (like `Money`), and pure business
rules, with no knowledge of Telegram, SQL, or any framework.

### Composition Root
The single place where concrete adapters are wired to the core (dependency
injection). The only place that "knows" about every technology at once.

### Mutability category
Every table is classified as **strictly append-only** (no update/delete of any
row, ever), **controlled-mutable** (specific fields may change under specific
audited rules), or **mutable** (ordinary reference/config data). The full
classification is the *mutability matrix* in
[`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md).
