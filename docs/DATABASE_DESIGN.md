# Database Design

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Engine: **PostgreSQL**. Migrations: **Alembic**. This schema realizes the rules
> in [`BUSINESS_RULES.md`](./BUSINESS_RULES.md). Nothing here may store donor
> identity (invariant I1).

---

## 1. Design principles

- **Append-only financial data.** No `UPDATE`/`DELETE` on ledger rows;
  corrections are new reversal rows (BR-L). Enforced by triggers **and** by a
  least-privilege DB role (§11).
- **Money as `BIGINT` minor units (tiyin).** Never floats.
- **UUID primary keys** for entities that may later be exposed across adapters,
  avoiding enumeration; plus a **separate human-friendly `reference_no`** for
  ledger entries. Internal lookup tables use small integer identities.
- **UTC timestamps** (`timestamptz`) everywhere; report bucketing converts to the
  org time zone at query time (BR-R4).
- **No donor columns anywhere.** No table has a donor FK, name, phone, Telegram
  ID, or username tied to a donation. Structural guarantee.
- **Explicit mutability.** Every table is classified in the **mutability matrix**
  (§2); the immutability guarantees and the DB grant model both follow it.

---

## 2. Mutability matrix (authoritative)

| Table | Category | What may change | How enforced |
|-------|----------|-----------------|--------------|
| `ledger_entries` | **Strictly append-only** | Nothing (insert only) | Trigger blocks UPDATE/DELETE; app role lacks UPDATE/DELETE |
| `entry_annotations` | **Controlled-mutable** | `content` may be overwritten with a tombstone **only** as a redaction (sets `redacted_at`/`redacted_by`). No delete. | Trigger permits only the redaction shape of UPDATE |
| `audit_logs` | **Strictly append-only** | Nothing | Trigger + grant |
| `settings_history` | **Strictly append-only** | Nothing | Trigger + grant |
| `donation_accounts` | **Strictly append-only** | Nothing (a change = a new row) | Trigger + grant |
| `settings` | Mutable (config) | value | every change also writes `settings_history` |
| `staff_users` | Controlled-mutable | `is_active`, `deactivated_at`, `display_name`; never deleted | app logic + audit |
| `user_roles` | Mutable | assignments inserted/removed | audited |
| `roles`, `permissions`, `role_permissions` | Mutable (config) | presets protected via `is_system` | audited |
| `expense_categories` | Mutable (config) | `is_active`, `name`; never hard-deleted while referenced | audited |

> **Key correction from the review:** `donation_accounts` is now *truly*
> append-only — there is no `is_active`/`retired_at` field to update. "Active" is
> **derived** as the most recently created row (§6). This removes the earlier
> contradiction between "append-only" and "retire the old row".

---

## 3. ER overview (v1)

```
                      ┌───────────────┐        ┌────────────────┐
                      │    roles      │◀──────▶│  permissions   │
                      └──────┬────────┘  role_ └────────────────┘
                             │           perms
                    user_roles│
                             ▼
┌───────────────┐     ┌───────────────┐
│  audit_logs   │────▶│  staff_users  │  (staff + one reserved SYSTEM actor;
└───────────────┘     └──────┬────────┘   NEVER donors)
        ▲                    │ recorded_by / author
        │                    ▼
        │            ┌──────────────────┐       ┌────────────────────┐
        └────────────│  ledger_entries  │──────▶│  entry_annotations │
                     │ (donations +     │ 1:N   │ (private, redactable)│
                     │  expenses,       │       └────────────────────┘
                     │  append-only)    │◀───┐ reverses_entry_id
                     └────────┬─────────┘    └── (reversal → its original; UNIQUE)
                              │
                              ▼
                     ┌────────────────────────┐
                     │ (view) ledger_effective │  derives signed/effective amounts
                     └────────────────────────┘

┌────────────────────┐   ┌───────────────────────┐   ┌───────────────────┐
│ donation_accounts  │   │ settings / settings_hist│  │ expense_categories│
│ (append-only)      │   │                         │  └───────────────────┘
└────────────────────┘   └───────────────────────┘

Deferred to Version 2 (NOT in v1): attachments (receipts).
Future (post-v1): external_transactions (bank/payment imports).
```

---

## 4. Access control tables

### `staff_users`
Only Treasurers, Super Admins, and **one reserved system actor**. **Never**
donors/public users.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `telegram_id` | `bigint` NULL | authorization key; **NULL for the system actor** |
| `display_name` | `text` NULL | operator's name for audit readability (staff, not donor) |
| `is_system` | `boolean` NOT NULL DEFAULT false | true only for the reserved system actor |
| `is_active` | `boolean` NOT NULL DEFAULT true | deactivation, never hard delete |
| `created_at` | `timestamptz` NOT NULL | |
| `created_by` | `uuid` NULL FK→staff_users | null for the seeded first admin & system actor |
| `deactivated_at` | `timestamptz` NULL | |

- Partial unique index on `telegram_id` `WHERE telegram_id IS NOT NULL`.
- `CHECK`: `is_system` ⇒ `telegram_id IS NULL`; non-system ⇒ `telegram_id NOT NULL`.
- At most one system actor (partial unique index `WHERE is_system`).
- The system actor cannot log in (no telegram_id) and is authorized only by
  execution context (BR-SY).

### `roles`
| `id` `smallint` PK | `code` `text` UNIQUE (`user`,`treasurer`,`super_admin`) | `name` `text` | `is_system` `boolean` (presets can't be deleted) |

### `permissions`
| `id` `smallint` PK | `code` `text` UNIQUE (e.g., `donation.record`) | `description` `text` |

### `role_permissions` (M:N)
`role_id` FK→roles · `permission_id` FK→permissions · PK(role_id, permission_id)

### `user_roles` (M:N)
`staff_user_id` FK→staff_users · `role_id` FK→roles · `assigned_at` · `assigned_by` FK→staff_users · PK(staff_user_id, role_id)

> The **User (public)** role exists as a row for completeness, but public users
> are never inserted into `staff_users`; their permissions are granted by default
> in the application layer.

---

## 5. Ledger (the heart)

### `ledger_entries`
Holds donations, expenses, and reversal entries. **Strictly append-only.**
A reversal stores **no financial data of its own** — amount, direction, kind,
currency and event time are **derived from the original** it points to (BR-L3).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `reference_no` | `bigint` GENERATED ALWAYS AS IDENTITY, UNIQUE NOT NULL | human-friendly public id (`#1042`) (BR-L8) |
| `entry_role` | `text` NOT NULL | `original` \| `reversal` |
| `entry_kind` | `text` NULL | `donation` \| `expense`; NOT NULL for original, NULL for reversal (derived) |
| `amount_minor` | `bigint` NULL | tiyin; NOT NULL & `> 0` for original; **NULL for reversal** |
| `currency` | `char(3)` NULL | `'UZS'`; NOT NULL for original; NULL for reversal |
| `source` | `text` NULL | donation original only: `cash` \| `bank_manual` \| `bank_api` |
| `expense_category_id` | `smallint` NULL FK→expense_categories | expense original only |
| `expense_description` | `text` NULL | **public** usage description; NOT NULL for expense original; NULL otherwise |
| `event_at` | `timestamptz` NULL | when money moved; NOT NULL for original; NULL for reversal (derived) |
| `recorded_at` | `timestamptz` NOT NULL DEFAULT now() | system record time |
| `recorded_by` | `uuid` NOT NULL FK→staff_users | human staff, or the system actor |
| `reverses_entry_id` | `uuid` NULL FK→ledger_entries, UNIQUE | set only for reversal (BR-L3 "one reversal per entry") |

**Constraints & triggers**
- `UNIQUE (reverses_entry_id)` — at most one reversal per entry (BR-L3, BR-C2).
- `CHECK (entry_role IN ('original','reversal'))`.
- `CHECK` **original ⇒** `entry_kind NOT NULL`, `amount_minor NOT NULL AND amount_minor > 0`, `currency NOT NULL`, `event_at NOT NULL`, `reverses_entry_id NULL`.
- `CHECK` **reversal ⇒** `entry_kind NULL`, `amount_minor NULL`, `currency NULL`, `source NULL`, `expense_category_id NULL`, `expense_description NULL`, `event_at NULL`, `reverses_entry_id NOT NULL`.
- `CHECK` donation original ⇒ `source NOT NULL`, `expense_category_id NULL`, `expense_description NULL`.
- `CHECK` expense original ⇒ `expense_category_id NOT NULL`, `expense_description NOT NULL`, `source NULL`.
- **Trigger**: a reversal's target must exist and be `entry_role='original'`
  (cannot reverse a reversal — BR-L3).
- **Trigger**: block all `UPDATE`/`DELETE` (strictly append-only).
- Indexes: `event_at`, (`entry_kind`,`event_at`), `recorded_by`, `reverses_entry_id`.

> **Why a reversal stores no amount:** the review found that storing the amount on
> both rows lets a bad insert create a reversal that cancels a *different* amount.
> By deriving the reversal's effect from its target, that class of bug/tamper is
> impossible (BR-L3, ADR-0010).

### `entry_annotations`
All optional staff free text (context **notes** and required **reversal reasons**).
**Private (staff-only). Controlled-mutable:** insert freely; the only permitted
update is a **redaction**. No delete.

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `ledger_entry_id` | `uuid` NOT NULL FK→ledger_entries | |
| `annotation_type` | `text` NOT NULL | `note` \| `reversal_reason` |
| `author_id` | `uuid` NOT NULL FK→staff_users | |
| `content` | `text` NOT NULL | overwritten with a tombstone on redaction |
| `created_at` | `timestamptz` NOT NULL DEFAULT now() | |
| `redacted_at` | `timestamptz` NULL | set on PII-erasure |
| `redacted_by` | `uuid` NULL FK→staff_users | set on PII-erasure |

- Every `reversal` entry has **exactly one** `reversal_reason` annotation, created
  in the same transaction (satisfies BR-L5). A partial unique index enforces one
  `reversal_reason` per entry.
- **Trigger**: permit `UPDATE` only when it is a valid redaction (sets
  `redacted_at`, `redacted_by`, replaces `content` with the tombstone); block
  `DELETE`. This is the sole content mutation in the system (BR-X, ADR-0009).
- Never exposed to public users (BR-P1).

### View `ledger_effective` (derived, not stored)
Resolves each row to its effective values; reversals join to their target:

```
original: effective_kind = entry_kind
          effective_amount_minor = amount_minor
          effective_event_at = event_at
          signed_minor = (entry_kind='donation' ?  amount_minor : -amount_minor)

reversal (join target o):
          effective_kind = o.entry_kind
          effective_amount_minor = o.amount_minor
          effective_event_at = o.event_at
          signed_minor = (o.entry_kind='donation' ? -o.amount_minor : o.amount_minor)

is_reversed(original) = EXISTS(reversal r WHERE r.reverses_entry_id = original.id)
```
`balance = SUM(signed_minor)`; a reversed pair nets to zero automatically. All
reports/statistics read from this view (BR-R).

### `expense_categories`
`id` `smallint` PK · `code` `text` UNIQUE · `name` `text` · `is_active` `boolean`.
Extensible, admin-managed (`category.manage`). Seeded (aid, utilities,
construction, salaries, other, …). Never hard-deleted while referenced.

---

## 6. Donation account (public destination) — true append-only

### `donation_accounts`
A change to the account is a **new row**; the **active** account is derived as the
latest by `created_at`. No row is ever updated or deleted (BR-AC, mutability
matrix).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `label` | `text` NOT NULL | e.g., "Main card" |
| `account_type` | `text` NOT NULL | `card` \| `bank_account` \| `wallet` \| `disabled` |
| `account_value` | `text` NULL | public card/account number; NULL when `disabled` |
| `holder_name` | `text` NULL | organization's account holder (not a donor) |
| `created_at` | `timestamptz` NOT NULL | |
| `created_by` | `uuid` NOT NULL FK→staff_users | |

- **Active account** = `SELECT ... ORDER BY created_at DESC LIMIT 1`.
- To stop accepting donations, insert a row with `account_type='disabled'`.
- Full history (every past account) is preserved and visible to admins;
  changes are audited (BR-AC4).

---

## 7. Settings

### `settings`
Typed key/value for runtime configuration (distinct from deploy-time env vars in
[`CONFIGURATION.md`](./CONFIGURATION.md)). **Mutable**, but every change also writes
`settings_history`.

| `key` `text` PK | `value` `jsonb` NOT NULL | `updated_at` `timestamptz` | `updated_by` `uuid` FK→staff_users |

Keys include `org.name`, `org.timezone`, `expenses.block_overspend`,
`limits.amount_warn_threshold`, `limits.amount_max`, `limits.backdate_window_days`
(see [`CONFIGURATION.md`](./CONFIGURATION.md)).

### `settings_history`
Append-only: `key`, `old_value`, `new_value`, `changed_by`, `changed_at`.

---

## 8. Audit

### `audit_logs`
Append-only. Staff/system-actor identities only; never donor identity, never
copied redacted PII (BR-AU3).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `actor_user_id` | `uuid` NULL FK→staff_users | system actor for machine actions |
| `action` | `text` NOT NULL | e.g., `donation.recorded`, `entry.reversed`, `annotation.redacted`, `role.assigned` |
| `entity_type` | `text` NOT NULL | e.g., `ledger_entry`, `staff_user` |
| `entity_id` | `uuid` NULL | |
| `entity_ref` | `bigint` NULL | ledger `reference_no` where applicable |
| `summary` | `jsonb` NULL | structured before/after key fields (no donor data, no free-text PII) |
| `created_at` | `timestamptz` NOT NULL DEFAULT now() | |
| `context` | `jsonb` NULL | channel=telegram, correlation id (no PII) |

- Reversal audit records the reference and links to the reversal; the **reason
  text is not duplicated** into the audit row (it lives in the redactable
  annotation), so redaction can't leave a stale copy.
- Indexes: `created_at`, `actor_user_id`, (`entity_type`,`entity_id`).
- **Restore caveat:** a database restore can wipe this table, so restore events
  are additionally logged **off-box** by the operator (BR-AU5;
  [`DEPLOYMENT.md`](./DEPLOYMENT.md), [`SECURITY.md`](./SECURITY.md)).

---

## 9. Deferred to Version 2 — attachments (receipts)

Receipts are **not implemented in v1**. When added in V2, the planned shape is an
`attachments` table (`ledger_entry_id`, `storage_key`, `content_type`,
`byte_size`, `is_sensitive` default true, `uploaded_by`, timestamps) with files
stored outside the database, sensitive-by-default access control, and the same
PII-erasure principle. It is listed here only to reserve the design space; do not
build it in v1. See [`ROADMAP.md`](./ROADMAP.md).

---

## 10. Future (post-v1) — external transactions

### `external_transactions`
Raw imports from Click/Payme/Uzcard/Humo/bank APIs, separate from the ledger for
idempotent, auditable reconciliation. See
[`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md).

| Column | Type | Notes |
|--------|------|-------|
| `id` | `uuid` PK | |
| `provider` | `text` NOT NULL | `click` \| `payme` \| `uzcard` \| `humo` \| `bank_x` |
| `provider_txn_id` | `text` NOT NULL | provider's unique id |
| `amount_minor` | `bigint` NOT NULL | |
| `currency` | `char(3)` NOT NULL | |
| `occurred_at` | `timestamptz` NOT NULL | |
| `raw_payload` | `jsonb` NOT NULL | **screened**: donor-identifying fields removed before persistence |
| `status` | `text` NOT NULL | `imported` \| `matched` \| `ignored` |
| `matched_entry_id` | `uuid` NULL FK→ledger_entries | the donation it produced (authored by the system actor) |
| `imported_at` | `timestamptz` NOT NULL DEFAULT now() | |

- `UNIQUE (provider, provider_txn_id)` → idempotency (BR-C3).
- ⚠️ Payloads must be screened for PII before persistence (I1;
  [`SECURITY.md`](./SECURITY.md), [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md)).

---

## 11. Enforcing the model at the database

Application code enforces the rules; the DB adds defense in depth aligned with the
mutability matrix (§2):

1. **Constraints** as above (unique reversal, checks, partial unique indexes).
2. **Triggers**:
   - Strictly append-only tables (`ledger_entries`, `audit_logs`,
     `settings_history`, `donation_accounts`): `RAISE EXCEPTION` on
     `UPDATE`/`DELETE`.
   - `entry_annotations`: allow `INSERT`; allow `UPDATE` **only** when it matches
     the redaction shape; block `DELETE`.
3. **Two DB roles** (least privilege):

| Role | ledger_entries / audit_logs / settings_history / donation_accounts | entry_annotations | settings / staff_users / expense_categories / user_roles / roles* |
|------|--------------------------------------------------------------------|-------------------|--------------------------------------------------------------------|
| **`APP_DB_USER`** (bot) | `INSERT`, `SELECT` | `INSERT`, `SELECT`, `UPDATE` (redaction; further constrained by trigger) | `INSERT`, `SELECT`, `UPDATE`, and `DELETE` on `user_roles` |
| **`MIGRATION_DB_USER`** | full DDL/DML | full | full |

The app role has **no** `UPDATE`/`DELETE` on strictly append-only tables — so even
a code bug or SQL injection cannot rewrite financial history. Migrations run under
the separate privileged role. Exact DDL/trigger bodies are produced in Phase 3
consistent with this design.

---

## 12. Migrations & seeding

- **Alembic** manages all schema. `create_all` is **not** used in production.
- **Seed** (idempotent, on first run):
  - Roles: `user`, `treasurer`, `super_admin` (system).
  - Permission catalog (from [`USER_ROLES.md`](./USER_ROLES.md)).
  - `role_permissions` mapping per the preset matrix.
  - The reserved **system actor** `staff_users` row (`is_system=true`,
    `telegram_id NULL`).
  - Default `expense_categories`.
  - The **first Super Admin** row from the env-configured Telegram ID (idempotent;
    doubles as break-glass recovery — see [`USER_ROLES.md`](./USER_ROLES.md)).
  - Default `settings` (org timezone `Asia/Tashkent`, overspend policy, amount
    limits, backdate window).

---

## 13. Retention & privacy

- There is **no donor data** to retain or purge — by design.
- The one erasure path is **PII redaction** of `entry_annotations.content` (and
  reversal-reason annotations), used only to remove leaked donor identity
  (BR-X; [`SECURITY.md`](./SECURITY.md)).
- Ledger, audit, settings history, and donation-account history are retained
  indefinitely for transparency. Backups follow [`DEPLOYMENT.md`](./DEPLOYMENT.md).
