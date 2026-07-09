# Testing Strategy

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> How we guarantee correctness — especially of money, the immutable ledger, the
> anonymity guarantee, and the public/private split — over the life of the project.

---

## 1. What must never break (test priorities)

In priority order, tests exist first and foremost to protect the **invariants**
from [`BUSINESS_RULES.md`](./BUSINESS_RULES.md) §13:

1. **I1 — No donor identity.** No code path can persist donor identity; donations
   have no public free text.
2. **I2/I3 — Immutable ledger; reversal-only; single reversal; reversal amount
   derived from the original.**
3. **I4 — Money is integer minor units; arithmetic is exact.**
4. **I5 — Reports are derived and reproducible.**
5. **I6 — Every privileged action is audited; restore is logged off-box.**
6. **I7 — Donor-context free text lives only in private, staff-only annotations
   and is PII-redactable; nothing donor-related is ever public.**
7. **Authorization** — permissions enforced in the application layer.

Every one of these has dedicated tests described below.

---

## 2. The test pyramid

```
        ▲  fewer, slower
        │   E2E / bot-flow tests (aiogram handlers, mocked Telegram)
        │   Integration tests (repositories vs real PostgreSQL)
        │   Unit tests (domain + application; no I/O)   ← the bulk
        ▼  many, fast
```

The hexagonal architecture makes the **bulk of tests fast and pure**: domain and
application logic run with in-memory fakes, no Telegram, no database.

### 2.1 Unit tests (domain + application)
- **Domain:** `Money` arithmetic and currency-mixing rejection; ledger entity
  rules (positive amount, reversal effect **derived** from the target, "reversed"
  is computed); annotation redaction rule; permission resolution.
- **Application (use cases with fake ports):** `RecordDonation`, `RecordExpense`,
  `ReverseEntry`, `AddAnnotation`, `RedactAnnotation`, `GenerateReport`,
  `GetStatistics`, `ManageStaff`, `ConfigureDonationAccount`, `UpdateSetting`,
  etc. — using in-memory repositories and a fake `Clock`.
- Fast, deterministic, no external dependencies.

### 2.2 Integration tests (persistence)
- Run against a **real PostgreSQL** (ephemeral container).
- Verify the **mutability matrix** ([`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md)
  §2, §11) is actually enforced:
  - `UPDATE`/`DELETE` on `ledger_entries`, `audit_logs`, `settings_history`,
    `donation_accounts` are rejected by triggers.
  - `entry_annotations` accepts inserts and **only** redaction-shaped updates;
    `DELETE` is rejected.
  - `UNIQUE(reverses_entry_id)` prevents double reversal under concurrency.
  - The least-privilege `APP_DB_USER` genuinely lacks `UPDATE`/`DELETE` on the
    strictly append-only tables.
- Verify the `ledger_effective` view computes balances correctly, including
  reversed pairs netting to zero.
- Verify migrations apply cleanly and seed data (roles, permissions, **system
  actor**, categories, first admin, default settings) is correct and idempotent.

### 2.3 End-to-end / bot-flow tests
- Exercise aiogram handlers with a **mocked Telegram** layer, asserting the right
  use case is called with the right command and the right localized reply is
  produced (including the `#reference_no` in confirmations).
- Cover key flows from [`BOT_FLOW.md`](./BOT_FLOW.md): record donation/expense,
  reverse, add private note, redact, view report, manage staff/categories,
  unauthorized access. Assert there is **no** restore action in the bot.

---

## 3. Specific correctness tests

### 3.1 Money
- Parsing "5 000" so'm → `500000` tiyin; formatting back is exact.
- No floating point anywhere in money paths (enforced by type + review).
- Rejects amount ≤ 0; enforces warn-threshold confirmation and hard max (BR-M4).

### 3.2 Ledger & balance (property-based where useful)
- Balance = Σ effective signed amount for random sequences of donations/expenses.
- A reversed pair contributes exactly zero to the balance.
- **A reversal has no independent amount** — its effect always equals the negation
  of its target; there is no way to make it cancel a different amount (I3).
- Reversing an already-reversed entry is rejected (BR-L3).
- A reversal cannot target another reversal.
- Original rows are byte-for-byte unchanged after a reversal (no mutation).
- `event_at` outside the allowed window is rejected; within-window back-dating is
  accepted (BR-L7).

### 3.3 Reports (reproducibility & time zone)
- Same ledger + same period + same `org.timezone` ⇒ identical numbers (run twice).
- Day/month/year bucketing uses `org.timezone`; an entry near midnight lands in
  the correct local day (`Asia/Tashkent` boundary tests).
- Adding a correction changes future output only by adding entries, never by
  altering historical rows.
- Public report output includes expense usage descriptions but **never** any
  private text (annotations, reversal reasons).

### 3.4 Anonymity & public/private (I1, I7) — guard tests
- **Schema guard:** an automated test asserts that no table reachable from a
  donation has a donor-identity column (name/phone/username/telegram_id), so a
  future migration can't silently reintroduce one.
- **Command guard:** `RecordDonation`'s input type has no donor-identity field and
  no public free-text field (interface-level test).
- **Public-surface guard:** report/statistics/account read paths never return
  annotation or reversal-reason content.
- **Log guard:** for public-user interactions, the Telegram ID is not written to
  any persistent store or log; private free text is never logged.
- **Future integration guard** *(post-v1)*: given a provider payload containing a
  name, the screening step yields a record with only amount/time/provider/txn id.

### 3.5 Annotations & PII-erasure (I7)
- Annotations are private: no public path returns them.
- Adding an annotation after recording is an insert and does not mutate the entry.
- `RedactAnnotation` overwrites content with the tombstone, sets
  `redacted_at`/`redacted_by`, and requires `pii.erase`.
- The redaction audit entry records the event **without** copying the redacted
  text; the audit log never contains the leaked text (BR-X4).
- Every `reversal` entry has exactly one `reversal_reason` annotation, written in
  the same transaction.

### 3.6 Authorization
- Each privileged use case rejects callers lacking the required permission
  (checked against the v1 catalog in [`USER_ROLES.md`](./USER_ROLES.md)).
- Unregistered users get only the default public permissions.
- Deactivated staff lose access immediately.
- The **system actor** cannot be invoked as a human/login principal.

### 3.7 Audit (I6)
- Every state-changing use case writes exactly one audit entry, in the **same
  transaction** as the change (atomicity: force a failure, assert neither the
  change nor the audit row persists).
- Audit entries never contain donor identity or redacted free text.

### 3.8 Backups & the restore boundary
- The bot exposes backup create/list/download but **no** restore action (assert
  its absence).
- Backup jobs are authored by the system actor and audited; a simulated missed run
  triggers a catch-up on start.

> **Receipts:** no receipt tests in v1 — receipts are a Version 2 feature; their
> tests (default-sensitive, never-public, access-controlled) will be added then.

---

## 4. Tooling & conventions (targets for Phase 3)

- **Test runner:** `pytest` (with `pytest-asyncio` for async paths).
- **Property-based:** `hypothesis` for ledger/money invariants.
- **DB for integration:** ephemeral PostgreSQL container (via test fixture),
  never SQLite for integration — triggers/constraints/grants must be the real
  engine.
- **Coverage:** the goal is *invariant coverage*, not a vanity percentage.
- **CI:** run unit + integration + e2e on every change; block merge on failure or
  on any anonymity/immutability/public-private guard test failing.
- **Non-flaky:** deterministic clock via the `Clock` port; no real network.

> Note: exact tool versions and CI configuration are finalized in Phase 3; this
> document fixes the **strategy** and the **must-have** tests.

---

## 5. Definition of done (per feature)

A feature is "done" only when:
- Relevant invariants have tests (not just happy-path).
- Unit + integration tests pass locally and in CI.
- Authorization and audit are covered for any privileged action.
- Documentation (this set) reflects any rule/schema change, with an ADR if the
  change is architectural.
