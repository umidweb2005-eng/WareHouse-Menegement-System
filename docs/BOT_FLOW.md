# Bot Flow (Telegram UX)

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> The Telegram bot is one **inbound adapter**; every action here calls a use case
> in the application layer. All text is localized (v1: Uzbek). This document
> describes behavior, not implementation.

---

## 1. Principles for the bot layer

- **No business logic in handlers.** Handlers collect input, call a use case,
  render the result.
- **Anonymity first.** For public users, the bot uses the Telegram ID only to
  reply; it is never written to any store (invariant I1).
- **Public vs private.** The bot never shows private information (annotations,
  reversal reasons, audit) to public users; it only exposes reports, statistics,
  the donation account, and public expense usage descriptions (BR-P).
- **Localized, friendly, minimal.** Short messages, inline keyboards, clear
  confirmations. v1 in Uzbek; strings come from the i18n catalog.
- **Idempotent navigation.** Menus are re-entrant; `/start` and a persistent menu
  always return the user to a known state.
- **Least privilege UI.** Users only see buttons for actions they may perform;
  the server still re-checks every permission.

---

## 2. Entry points & menu (by effective role)

`/start` → the bot resolves the caller's Telegram ID → permissions → renders the
matching menu.

**Public user menu**
- 📊 Reports (day / month / year / all-time)
- 📈 Statistics
- 💳 How to donate (donation account)
- ℹ️ About / transparency note
- 🌐 Language (designed-for; v1 shows Uzbek only)

**Treasurer menu** = public menu **plus**
- ➕ Record donation
- ➖ Record expense
- 🧾 Recent entries (view · reverse · add private note)

**Super Admin menu** = treasurer menu **plus**
- 👥 Manage staff (add/deactivate, assign roles)
- 🏷 Manage expense categories
- ⚙️ Settings
- 💳 Configure donation account
- 🗂 Audit log
- 🧹 Redact leaked identity (PII-erasure)
- 💾 Backups (run · download · list)

> **Restore is deliberately absent from the bot.** It is an operator-only host
> procedure (see [`DEPLOYMENT.md`](./DEPLOYMENT.md)), because a restore can rewrite
> the entire immutable ledger and must never be a single-tap action.

---

## 3. Public flows

### 3.1 View reports
```
User → 📊 Reports
Bot  → choose period: [Today] [This month] [This year] [All time] [Custom]
User → picks period
Bot  → renders: total received, total spent, net balance, entry counts,
        and expense category breakdown WITH public usage descriptions
        all derived from the ledger (BR-R1); amounts formatted in so'm
```
- Custom range asks for start/end dates (validated, org time zone).
- No donor information is present anywhere — there is none. No private text
  (annotations, reversal reasons) is ever shown here.

### 3.2 View statistics
```
User → 📈 Statistics
Bot  → trend (e.g., monthly inflow/outflow), top expense categories,
        averages — all aggregate, all from the ledger
```

### 3.3 How to donate
```
User → 💳 How to donate
Bot  → shows the active donation account (label, type, number, holder)
        + a short instruction and the transparency promise
```
- The active account is the most recently configured one (BR-AC). The bot does
  **not** collect a donation here in v1; donors pay via the shown account.
  (Future: inline payment via Click/Payme — see API_INTEGRATIONS.md.)

---

## 4. Treasurer flows

### 4.1 Record a donation (FSM)
```
Treasurer → ➕ Record donation
Bot  → "Amount (so'm)?"           → validate > 0, parse to tiyin
        → if ≥ warn threshold: extra "Confirm large amount?" step (BR-M4)
        → if > max: reject with explanation
Bot  → "Source?" [Cash] [Bank transfer]
Bot  → "Date/time of receipt?" [Now] [Pick date]   (event_at)
        → must not be in the future; back-dating beyond the window is rejected;
          back-dating within the window asks for confirmation (BR-L7)
Bot  → "Add a private note? (optional — staff-only; do NOT enter donor names)"
        [Skip] [Add note]        → stored as a private annotation (BR-N)
Bot  → Summary + [Confirm] [Cancel]
Confirm → use case RecordDonation → persists entry (+ optional annotation) + audit
          in one transaction
Bot  → "✅ Donation recorded. Reference: #<reference_no>"
```
Guardrails:
- The note is **private** and its prompt warns against entering donor identity.
- Donations have **no public free text**; no field ever asks "who donated?".
- Receipts are **not** part of v1 (Version 2 feature).

### 4.2 Record an expense (FSM)
```
Treasurer → ➖ Record expense
Bot  → "Amount (so'm)?"                 → > 0 (same large-amount rules, BR-M4)
Bot  → "Category?" [Aid][Utilities][Construction][Salaries][Other]  (managed list)
Bot  → "Usage description? (PUBLIC — what the money was used for)"   (required)
Bot  → "Date/time?" [Now] [Pick date]   (same event_at rules, BR-L7)
Bot  → Summary + [Confirm] [Cancel]
Confirm → RecordExpense use case
Bot  → "✅ Expense recorded. Reference: #<reference_no>"
        (+ warning if balance goes negative; blocks only if policy = block, BR-E4)
```
- The description is **public** (shown in reports); staff are told never to place
  any personal identity there (BR-P2).

### 4.3 Recent entries — view, reverse, annotate
```
Treasurer → 🧾 Recent entries
Bot  → list (own entries first): #ref · kind · amount · date · reversed?
User → selects #ref → [View] [Reverse] [Add private note]

View       → shows the entry + its private annotations (staff-only)
Add note   → free text → appended as a private annotation (BR-N; never edits the entry)

Reverse → Bot asks "Reason for correction? (required, private)" (BR-L5)
        → Bot shows the effect ("this cancels #ref; amount is taken from the
          original") + [Confirm]
Confirm → ReverseEntry use case (reason saved as a private reversal_reason annotation)
          - blocks if already reversed (BR-L3) → "This entry was already corrected."
          - a reversal cannot target another reversal
Bot  → "✅ Correction posted as #<new_ref>. To fix a value, record a new correct entry."
```
- Editing/deleting an entry is **never** offered — the UI has no such action (I2).
- Any treasurer may reverse any entry; every reversal is audited (see
  [`USER_ROLES.md`](./USER_ROLES.md) §4).

---

## 5. Super Admin flows

### 5.1 Manage staff
```
Admin → 👥 Manage staff
        [Add staff] [List staff]
Add   → "Telegram ID of new staff?" → "Role?" [Treasurer][Super Admin][Custom role]
        → creates staff_users row + user_roles + audit
List  → select staff → [Assign role][Remove role][Deactivate]
```
- No self-signup. Only holders of `user.manage` reach this menu.
- Deactivate never deletes; the person loses access immediately.
- Recommendation surfaced in UI: keep at least two Super Admins (governance
  resilience, [`USER_ROLES.md`](./USER_ROLES.md) §5).

### 5.2 Manage expense categories
```
Admin → 🏷 Manage expense categories
        [List] [Add] [Rename] [Deactivate]
Each change → ManageCategory use case + audit
```
- Categories are never hard-deleted while referenced; they are deactivated
  (`category.manage`).

### 5.3 Settings
```
Admin → ⚙️ Settings
        - Organization name / time zone
        - Overspend policy (warn | block)            (BR-E4)
        - Large-amount warn threshold / hard max     (BR-M4)
        - Back-date window (days)                     (BR-L7)
        - Localization defaults (designed-for)
Each change → UpdateSetting use case → settings + settings_history + audit
```
- Changing the time zone warns that it re-buckets historical report days (BR-R5)
  and is audited.

### 5.4 Configure donation account
```
Admin → 💳 Configure donation account
        [View active] [Change] [Disable donations]
Change  → collect label, type [Card/Bank/Wallet], number, holder
          → inserts a NEW row (append-only); the newest row becomes active (BR-AC)
Disable → inserts a row with type=disabled
Bot     → "✅ Donation account updated. Public users now see the new account."
```

### 5.5 Audit log
```
Admin → 🗂 Audit log
        filter by [actor][action][date range] → paginated list
        each item: who, what, when, target #ref (never donor data, never redacted PII)
```

### 5.6 Redact leaked identity (PII-erasure)
```
Admin → 🧹 Redact leaked identity
        → locate the annotation / reversal reason containing the leak (by #ref)
        → [Confirm redaction] (irreversible; explain it removes the text for privacy)
Confirm → RedactAnnotation use case (pii.erase)
          → overwrites content with a tombstone; records redacted_at/by; audits
            the event WITHOUT copying the leaked text (BR-X)
Bot  → "✅ The text was redacted. Financial figures are unchanged."
```

### 5.7 Backups
```
Admin → 💾 Backups
        [Run backup now] [Download latest] [List backups]
Run     → triggers on-demand DB backup (BackupService, authored by system actor) + audit
```
- **No restore button.** Restore is an operator-only host procedure documented in
  [`DEPLOYMENT.md`](./DEPLOYMENT.md), logged off-box.

---

## 6. Scheduled (non-interactive) flows

Driven by the **scheduler adapter**, authored by the **system actor**, not a human:
- **Automatic backups** on a schedule ([`DEPLOYMENT.md`](./DEPLOYMENT.md)), with
  success/failure audited and admins notified on failure; a missed run (e.g., bot
  was down at the scheduled minute) is caught up on next start.
- **Periodic public report posting** to a channel/group — *designed-for, not in v1*.

---

## 7. Error & edge handling

| Situation | Bot behavior |
|-----------|--------------|
| Invalid amount (≤ 0, non-numeric) | Re-prompt with example; never crash |
| Amount ≥ warn threshold / > max | Extra confirmation / rejection (BR-M4) |
| Future or too-old `event_at` | Reject / confirm per BR-L7 |
| Unauthorized action | Generic "You don't have access to this." (no detail leak) |
| Reversing an already-reversed entry | "This entry was already corrected." |
| Trying to reverse a reversal | "You can't reverse a correction; record a new entry." |
| Unexpected/internal error | Friendly localized apology; details logged (no PII) |
| Unknown command / stray text | Show the menu again |
| Long operation (report/backup) | Acknowledge immediately, then send result |

---

## 8. Localization notes

- Every string above is a **catalog key**, not literal text. v1 provides Uzbek
  translations; adding Russian/English later means adding catalogs, not editing
  handlers.
- Number/date formatting is locale-aware in the presentation layer only.
- A future per-user language toggle stores preference for **staff** only (public
  users remain unstored); designed-for, not required in v1.

---

## 9. Mapping flows → use cases (traceability)

| Flow | Use case | Permission |
|------|----------|------------|
| View reports/stats | `GenerateReport`, `GetStatistics` | default public |
| How to donate | `GetActiveDonationAccount` | `account.view` |
| Record donation | `RecordDonation` | `donation.record` |
| Record expense | `RecordExpense` | `expense.record` |
| Reverse entry | `ReverseEntry` | `donation.reverse` / `expense.reverse` |
| Add private note | `AddAnnotation` | `entry.annotate` |
| Redact leaked identity | `RedactAnnotation` | `pii.erase` |
| Manage staff / roles | `ManageStaff`, `AssignRole` | `user.manage`, `role.manage` |
| Manage categories | `ManageCategory` | `category.manage` |
| Settings | `UpdateSetting` | `settings.manage` |
| Donation account | `ConfigureDonationAccount` | `account.manage` |
| Audit log | `QueryAuditLog` | `audit.view` |
| Backups (create/download) | `RunBackup`, `ListBackups` | `backup.manage` |
| Restore | *operator-only host procedure — not a bot use case* | n/a (host) |

> Use-case names here match [`PROJECT_ARCHITECTURE.md`](./PROJECT_ARCHITECTURE.md).
