# Business Rules

> The domain rules that the implementation **must** enforce. These are binding.
> Terms are defined in [`GLOSSARY.md`](./GLOSSARY.md).
> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)

---

## 1. Money

- **BR-M1.** All monetary amounts are stored as **integer minor units (tiyin)**,
  where `1 UZS = 100 tiyin`. Floating-point types are forbidden anywhere money is
  stored, computed, or transmitted internally.
- **BR-M2.** The single currency is **UZS**. A `currency` field is still stored
  on financial records (value `"UZS"`) so multi-currency can be added later
  without a migration of existing rows.
- **BR-M3.** Amounts must be **strictly positive** (`> 0`) when recording a
  donation or expense. Zero and negative amounts are rejected at the domain
  boundary.
- **BR-M4.** A configurable **sanity ceiling** guards against fat-finger errors:
  amounts above `limits.amount_warn_threshold` require an explicit extra
  confirmation, and amounts above `limits.amount_max` are rejected. Defaults are
  set in [`CONFIGURATION.md`](./CONFIGURATION.md); this is data-quality
  protection, not a business limit on generosity.
- **BR-M5.** Display formatting (grouping, "so'm" suffix, locale) happens only in
  the presentation layer. The core always speaks integer minor units.
- **BR-M6.** A `Money` value object encapsulates amount + currency and forbids
  mixing currencies in arithmetic. All money math goes through it.

---

## 2. The ledger (immutability)

The ledger is the append-only source of truth for donations and expenses.

- **BR-L1. Append-only.** Once a ledger entry is written, its fields are **never**
  updated and the row is **never** deleted. This holds for **all** roles,
  including Super Admin. (The only content that can ever change is free text in a
  separate annotation, and only via the audited PII-erasure path — §8.)
- **BR-L2. Corrections are reversals only.** To fix a mistake, post an
  **adjustment (reversal) entry** that references the original. If a corrected
  value is needed, post a new correct entry afterward. The original stays forever.
- **BR-L3. Reversal integrity.**
  - A reversal references exactly one original entry (`reverses_entry_id`).
  - An entry may be reversed **at most once** (enforced by a unique constraint on
    `reverses_entry_id`).
  - A reversal cannot itself be reversed (no chains). To undo a wrong reversal,
    post a fresh correct entry and audit it.
  - A reversal **does not store its own amount or direction**; they are **derived
    from the original entry** at read time. It is therefore impossible for a
    reversal to cancel a different amount than the original. (See
    [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) for how this is enforced.)
- **BR-L4. Derived state.** Whether an entry is "reversed" is **computed** from
  the existence of a reversal that references it — never stored as a mutable flag
  on the original row.
- **BR-L5. Reason required.** Every reversal must carry a non-empty human reason.
  It is stored (staff-only, §7) and surfaced in the audit log.
- **BR-L6. Immutable timestamps.** Each entry records both the **event time**
  (when the money actually moved — supplied by the treasurer) and the **record
  time** (when it was entered into the system — set by the system). Reports use
  event time; audit uses record time.
- **BR-L7. Event-time bounds.** `event_at` must not be in the future and must not
  be older than a configurable window (`limits.backdate_window_days`). Back-dating
  within the window is allowed but requires an explicit confirmation; anything
  outside the bounds is rejected. This prevents accidental date entry from
  silently corrupting historical reports.
- **BR-L8. Reference number.** Every ledger entry (including reversals) is assigned
  a **sequential, human-friendly `reference_no`** (e.g., `#1042`) at creation.
  It is used for selecting entries to reverse and for unambiguous reference. It is
  never reused and never changes.

---

## 3. Donations (inflow)

- **BR-D1.** Only a caller with `donation.record` may create a donation.
- **BR-D2.** A donation **must not** contain, reference, or allow entry of any
  donor identifier (name, Telegram ID, username, phone, etc.). This is enforced
  structurally: the donation has **no public free-text field** and no field
  capable of holding donor identity. See [`SECURITY.md`](./SECURITY.md).
- **BR-D3.** A donation captures: amount (BR-M rules), event date/time (BR-L7),
  and `source` (`cash` | `bank_manual` | `bank_api`). Optional context may be
  added as a **private annotation** (§6) — never as public text.
- **BR-D4.** Correcting a donation follows BR-L2 (reversal). Requires
  `donation.reverse`.
- **BR-D5.** Future automatic donations (`source = bank_api`) are created by the
  bank-integration adapter through the same use case, authored by the **system
  actor** (§9), and obey every rule here. *(Post-v1.)*

---

## 4. Expenses (outflow)

- **BR-E1.** Only a caller with `expense.record` may create an expense.
- **BR-E2.** An expense captures: amount, event date/time (BR-L7), a **category**
  (an extensible, admin-managed list — `category.manage`), and a required
  **public usage description** of what the money was used for. The description is
  public transparency data (§7) and must not contain donor identity.
- **BR-E3.** Expenses are subject to the same immutability and reversal rules as
  donations (BR-L). Correcting requires `expense.reverse`.
- **BR-E4. Overspend policy.** By default the system **warns** but does **not
  block** when an expense would drive the running balance negative (real-world
  timing gaps happen). Whether to hard-block is a `settings.manage` toggle. Note
  that, because the balance is a derived sum over an append-only ledger, a "block"
  check is **best-effort** under concurrency; it is a guard-rail, not a guarantee.

---

## 5. Balance & reporting

- **BR-R1. Everything is derived.** Every reported figure is computed from the
  ledger at query time. No total is ever typed in or stored as an editable number.
  v1 computes reports **directly in PostgreSQL**; no caching/materialized layer is
  used (it is a documented future optimization — see [`ROADMAP.md`](./ROADMAP.md)).
- **BR-R2. Balance formula.** The balance is the sum of **effective signed
  amounts**: a donation contributes `+amount`, an expense `−amount`, and a reversal
  contributes the negation of its target's effective amount (so a reversed pair
  nets to zero). Reversal amounts are derived (BR-L3), so the sum is always
  internally consistent.
- **BR-R3. Report periods.** Reports are available for **day**, **month**,
  **year**, and **all-time**, plus arbitrary custom ranges (designed-for).
- **BR-R4. Time zone.** Period bucketing uses the **organization time zone**
  (`Asia/Tashkent` by default). A "day" is a calendar day in that zone. Timestamps
  are stored in UTC and converted for reporting.
- **BR-R5. Reproducibility (per fixed time zone).** Given the same ledger state,
  the same period, and the same `org.timezone`, a report always produces the same
  numbers. Historical entries are never mutated, so corrections only ever *add*
  entries. Changing `org.timezone` re-buckets which calendar day an entry falls in
  — so the timezone is a parameter of reproducibility, and changing it after go-live
  is discouraged and audited (Asia/Tashkent has no DST, so the practical risk is
  low).
- **BR-R6. What a report contains.** Total received, total spent, net balance,
  entry counts, and an **expense category breakdown with public usage
  descriptions**. Public reports never reveal donor identity because none exists
  and donations carry no public text.
- **BR-R7. Public visibility.** Reports, statistics, the donation account, and
  expense usage descriptions are **public** to every bot user (`report.view`,
  `stats.view`, `account.view` granted by default). Everything else is private
  (§7).

---

## 6. Annotations (adding context without editing)

- **BR-N1.** Optional context on any entry is added as an **annotation** — an
  **append-only, private (staff-only)** note — never by editing the immutable
  entry. Requires `entry.annotate`.
- **BR-N2.** Annotations can be added at recording time or later; adding one is an
  *insert*, so it never violates ledger immutability.
- **BR-N3.** Annotations are **never public**. They are the intended place for
  staff context that might be sensitive.
- **BR-N4.** Annotation text (and a reversal reason) is the only content in the
  whole system that may be **redacted** — solely to remove leaked donor identity,
  via the audited PII-erasure path (§8). Redaction genuinely overwrites the text
  with a tombstone; it does not touch any financial field.

---

## 7. Public vs private information (explicit)

This separation is a first-class rule, not an implementation detail:

| Information | Visibility |
|-------------|-----------|
| Reports, statistics, balance | **Public** |
| Donation account details | **Public** |
| Expense **usage description** & category | **Public** |
| Donation amounts/dates (aggregated in reports) | **Public** (aggregate) |
| **Annotations** (staff context) | **Private (staff-only)** |
| **Reversal reasons** | **Private (staff-only)** |
| Audit log | **Private (Super Admin)** |
| Staff identities | **Private** |
| Donor identity | **Does not exist** |

- **BR-P1.** Donations have **no public free-text field**, so donor identity
  cannot leak through a public surface. Any donor-context risk is confined to
  private annotations, which are staff-only and redactable.
- **BR-P2.** Expense descriptions are public and must describe *spending* (vendor,
  purpose), which does not involve donors; staff are instructed never to place any
  personal identity there.

---

## 8. PII-erasure exception (privacy outranks immutability)

- **BR-X1.** Privacy is the highest principle. If donor identity is accidentally
  entered into free text (an annotation or a reversal reason), a Super Admin
  (`pii.erase`) may **redact** that specific text.
- **BR-X2.** Redaction **overwrites** the offending text with a tombstone (e.g.,
  `"[redacted: donor identity removed]"`) so the identity is genuinely gone from
  the database — not merely hidden.
- **BR-X3.** Redaction is **narrow**: it applies only to free-text fields
  (annotation content, reversal reason) and **never** to financial fields
  (amount, direction, dates, category), which remain strictly immutable.
- **BR-X4.** Every redaction is **audited** (who, when, which record, and that a
  redaction occurred) **without** copying the leaked text into the audit record.
- **BR-X5.** This is the single documented exception to append-only content; it
  exists because there is no acceptable alternative when a human leaks PII.

---

## 9. System actor (defined author for machine actions)

- **BR-SY1.** Records not created by a human — scheduled jobs and future automatic
  bank/payment imports — are authored by a reserved **system actor** principal, so
  every ledger entry and audit entry has a defined, non-null author.
- **BR-SY2.** The system actor cannot log in or use the bot and is never assigned
  to a person.
- **BR-SY3.** System-initiated writes still pass through the same use cases and
  produce the same audit trail; they are authorized by their execution context,
  not by a human permission check. *(The only v1 user of the system actor is the
  scheduled backup job; automatic donations are post-v1.)*

---

## 10. Audit

- **BR-AU1.** Every privileged, state-changing action writes an audit entry:
  recording/reversing entries, adding annotations, PII redaction, managing
  users/roles/categories/settings/account, and triggering backups.
- **BR-AU2.** Audit entries capture: actor (staff or system actor), action, target
  entity + `reference_no`, a structured before/after summary where applicable, and
  record time. They deliberately store **no free-text reason field**: a reversal's
  reason lives in its (redactable) `reversal_reason` annotation and is *referenced*
  by the target's reference — never copied into audit — so a later PII redaction
  cannot leave a stale copy (BR-X4).
- **BR-AU3.** Audit entries are **append-only** and never reference donor identity
  (there is none to reference), and never copy redacted PII or private free text.
- **BR-AU4.** Only `audit.view` (Super Admin) may read the audit log.
- **BR-AU5.** Because a database **restore** can wipe the in-database audit log,
  restore events are additionally recorded to an **off-box** log by the operator
  (see [`SECURITY.md`](./SECURITY.md) and [`DEPLOYMENT.md`](./DEPLOYMENT.md)).

---

## 11. Concurrency & consistency

- **BR-C1.** Writes that must be atomic (create entry + audit entry) occur in a
  single transaction (Unit of Work). Either both persist or neither does.
- **BR-C2.** The "at most one reversal per entry" rule (BR-L3) is enforced at the
  database level (unique constraint) so concurrent reversal attempts cannot both
  succeed.
- **BR-C3.** Idempotency for future automatic imports is enforced via a unique
  external transaction id; re-delivering the same bank event never creates a
  second donation. See [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md). *(Post-v1.)*

---

## 12. Receipts — deferred to Version 2

- **BR-RC1.** Receipt / file attachment support is **not part of v1**. This is a
  deliberate scope decision: it removes file-based donor-identity leakage from the
  first release. When introduced in V2, receipts will default to sensitive, be
  access-controlled, be storable outside the database, and be subject to the same
  PII-erasure principle. See [`ROADMAP.md`](./ROADMAP.md).

---

## 13. Invariants summary (quick reference)

| # | Invariant |
|---|-----------|
| I1 | No donation record can hold any donor identifier; donations have no public free text. |
| I2 | Ledger entries are never updated or deleted — by anyone. |
| I3 | Corrections are reversals; each entry is reversible at most once; reversal amount is derived from the original. |
| I4 | Money is integer minor units; never a float. |
| I5 | Every reported number is derived from the ledger. |
| I6 | Every privileged action is audited; restore is additionally logged off-box. |
| I7 | Donor-context free text lives only in private, staff-only annotations and is PII-redactable; nothing donor-related is ever public. |
| I8 | Reports bucket time in the org time zone; storage is UTC. |
