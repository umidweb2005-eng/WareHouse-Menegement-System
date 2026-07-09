# User Roles & Permissions (RBAC)

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Terms used here are defined in [`GLOSSARY.md`](./GLOSSARY.md).

---

## 1. Model: permission-based RBAC

Authorization is built on **fine-grained permissions**, grouped into **roles**,
assigned to **staff**. We deliberately do **not** hardcode three roles into the
business logic; instead:

```
Permission  ──many-to-many──▶  Role  ──many-to-many──▶  Staff user
```

- A **permission** is the smallest capability the system checks
  (e.g., `donation.record`).
- A **role** is a named bundle of permissions.
- **Roles are data**, not code. New roles (e.g., "Auditor", "Regional Treasurer")
  can be added later with zero code changes.
- Authorization checks are always written against **permissions**, never against
  role names. (Checking "does this user have `donation.record`?" — never "is this
  user a Treasurer?".) This keeps the door open for future roles.

The three presets below ship with v1.

---

## 2. Role presets (v1)

### User (Public) — implicit default
- **Not stored.** Applied automatically to any unregistered chat.
- Read-only, public-transparency capabilities.

### Treasurer
- Registered staff. Records donations and expenses, writes the public expense
  usage description, and may add private annotations and post reversals.
- Cannot manage roles, settings, users, categories, or backups.

### Super Admin
- Registered staff with full governance authority.
- The only role that can manage users, roles, settings, expense categories, the
  donation account, audit logs, backups, and the narrow PII-erasure action.

> **System actor** is *not* a role a person can hold. It is a reserved principal
> (see [`GLOSSARY.md`](./GLOSSARY.md)) used by scheduled jobs and future automatic
> imports; it has no login and is never assigned to a human.

---

## 3. Permission catalog (v1)

Permissions use a `resource.action` naming convention. This list is the initial
catalog; it is designed to grow.

| Permission code | Description | User | Treasurer | Super Admin |
|-----------------|-------------|:----:|:---------:|:-----------:|
| `report.view` | View reports (daily/monthly/yearly/total) | ✅ | ✅ | ✅ |
| `stats.view` | View statistics | ✅ | ✅ | ✅ |
| `account.view` | View the public donation account | ✅ | ✅ | ✅ |
| `donation.record` | Record a received donation | | ✅ | ✅ |
| `donation.reverse` | Post an adjustment/reversal for a donation | | ✅ | ✅ |
| `expense.record` | Record an expense (outflow) | | ✅ | ✅ |
| `expense.reverse` | Post an adjustment/reversal for an expense | | ✅ | ✅ |
| `entry.annotate` | Add a private annotation to an entry | | ✅ | ✅ |
| `user.manage` | Create/activate/deactivate staff | | | ✅ |
| `role.manage` | Create roles, assign permissions | | | ✅ |
| `category.manage` | Create/activate/deactivate expense categories | | | ✅ |
| `settings.manage` | Change system settings | | | ✅ |
| `account.manage` | Configure the donation account | | | ✅ |
| `audit.view` | View the audit log | | | ✅ |
| `pii.erase` | Redact leaked donor identity from free text (annotation / reversal reason) | | | ✅ |
| `backup.manage` | Trigger and download database backups | | | ✅ |

> **Restore is not an in-bot permission.** Restoring the database is a
> **operator-only host procedure** (see [`DEPLOYMENT.md`](./DEPLOYMENT.md) and
> [`SECURITY.md`](./SECURITY.md)), because a restore can rewrite the entire
> immutable ledger and must never be a single-tap action. `backup.manage` covers
> only creating and downloading backups.

> **Design note:** The public `User` capabilities (`report.view`, `stats.view`,
> `account.view`) are granted to *everyone*, including anonymous chats, because
> transparency is a core goal. They are listed as a role for consistency, but the
> system grants them by default without requiring registration.

> **Deferred to Version 2:** receipt/attachment permissions (`receipt.attach`,
> `receipt.view_sensitive`) are **not** part of v1 (receipts are a V2 feature —
> see [`ROADMAP.md`](./ROADMAP.md)). They will be added to this catalog when
> receipts ship.

---

## 4. Reversal scope (who may correct what)

- `donation.reverse` / `expense.reverse` permit reversing **any** matching entry,
  not only one's own. In a small, trusted treasury this is intentional (a
  colleague can fix a mistake when the original recorder is unavailable).
- **Every reversal is audited** with the acting staff member's identity and a
  required reason, so "who corrected what" is always answerable.
- The bot presents a treasurer's **own recent entries** first for convenience, but
  the underlying authorization is not scoped to ownership in v1.
- If an organization later needs stricter separation, an own-only variant
  (e.g., `entry.reverse.any` vs `entry.reverse.own`) can be added without redesign
  because checks live in the application layer (see §7).

---

## 5. Bootstrapping, onboarding & recovery

### First Super Admin
- The **first** Super Admin is defined via **environment variables** at
  deployment time (their Telegram ID). See [`CONFIGURATION.md`](./CONFIGURATION.md).
- On first startup, the system seeds the roles/permissions and grants the
  configured Telegram ID the Super Admin role.
- This is the **only** identity that can exist without being created by another
  admin. It solves the classic "who creates the first admin?" problem.

### Adding staff (chain of trust)
- Only a user with `user.manage` (Super Admin by default) can register new staff.
- New staff are added by their **Telegram ID** (obtained out-of-band). No
  self-service signup — this is a closed, trusted set of operators.
- Recommended onboarding flow (details in [`BOT_FLOW.md`](./BOT_FLOW.md)):
  1. Super Admin enters the new person's Telegram ID and chosen role.
  2. The system creates a staff record.
  3. The new staff member messages the bot; the bot recognizes their ID and
     unlocks their capabilities.

### Deactivation
- Staff are **deactivated**, never hard-deleted (their audit history must
  survive). A deactivated user loses all permissions immediately but remains
  referenced by past audit entries.

### Governance resilience (recommended)
- **Recommendation, not a hard requirement:** run with **at least two Super
  Admins** so the loss of one Telegram account does not lock out governance and so
  no single admin is entirely unchecked.
- **Break-glass recovery:** if all Super Admins are lost, an operator can
  re-seed the first Super Admin by setting `FIRST_SUPER_ADMIN_TELEGRAM_ID` and
  restarting; the seed step is idempotent and re-grants the Super Admin role to
  that Telegram ID. This recovery is an operator/host action and is out of reach
  of ordinary bot users. See [`DEPLOYMENT.md`](./DEPLOYMENT.md).

---

## 6. Authorization rules

1. Every privileged use case declares the permission it requires.
2. The Telegram adapter resolves the caller's Telegram ID → staff record →
   effective permissions (union of all assigned roles). Unregistered IDs get the
   default public permission set only.
3. If the caller lacks the required permission, the use case is **never invoked**
   and the attempt is logged (for privileged endpoints) without leaking why.
4. Permission checks live in the **application layer**, not in the Telegram
   handlers, so any future adapter (web, API) enforces the same rules.

---

## 7. Separation of duties (integrity)

To keep financial history trustworthy:

- Recording and correcting entries are **treasurer-level** actions, but every one
  is **audited** with the actor's identity.
- No role can **edit or delete** a ledger entry — corrections are reversals only,
  and context is added via append-only annotations (see
  [`BUSINESS_RULES.md`](./BUSINESS_RULES.md)). This is a *system-wide* invariant,
  not a per-role permission; **even Super Admins cannot mutate financial history.**
- The one deliberate exception is `pii.erase`: a Super Admin may redact **free
  text** (never financial fields) solely to remove leaked donor identity, and the
  redaction is itself audited (see [`SECURITY.md`](./SECURITY.md)).
- Managing **who** has power (`user.manage`, `role.manage`) is separated from
  **recording money** so an organization can split these duties across people.

---

## 8. Future expansion (designed-for)

- **New roles** (e.g., Auditor with `report.view` + `audit.view`, or a read-only
  board member) require only inserting role + role_permission rows.
- **New permissions** are added to the catalog and granted to roles as features
  ship — e.g., `receipt.attach` / `receipt.view_sensitive` (Version 2),
  `campaign.manage` when multi-campaign support arrives.
- **Scoped permissions** (e.g., per-campaign or per-fund, or own-only reversal)
  are anticipated: the permission model can be extended with an optional scope
  without redesign, because checks are abstracted behind the application layer.
