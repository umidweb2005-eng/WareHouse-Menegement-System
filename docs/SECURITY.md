# Security & Privacy

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Privacy is the project's highest principle. Where privacy and transparency
> conflict, **privacy wins** (see [`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md)).

---

## 1. The anonymity model

### 1.1 The core promise
The system **never persists donor identity**: no donor name, Telegram ID,
username, phone number, or any other identifier tied to a donation.

### 1.2 Why this is a *structural* guarantee, not a policy
Anonymity is enforced by **the absence of the capability to store identity**, not
by remembering to be careful:

- No donation-related table has a donor FK, name, phone, username, or Telegram ID
  column (see [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md)).
- The `RecordDonation` use case's input command has **no field** for donor
  identity, and donations carry **no public free text**. There is nowhere to put
  donor identity.
- Donations are recorded by **treasurers**, not by donors, so no donor session,
  contact, or profile is ever involved.

### 1.3 The two identity tiers (and why Telegram IDs still exist)
Telegram delivers the sender's ID to the bot on every update — unavoidable at the
protocol level. Our rule is about **persistence**:

| Tier | Whose ID | Persisted? | Reason |
|------|----------|-----------|--------|
| Public / donor | Anyone unregistered | **No** | Used transiently to reply, then discarded |
| Staff | Treasurers, Super Admins | **Yes** (`telegram_id`) | Required for authorization and audit |

Storing staff IDs does **not** violate donor anonymity: staff are operators, not
donors, and staff never appear on donation records.

### 1.4 The concrete leak risks (and how each is closed)

1. **A treasurer typing a donor's name into a private annotation.** ⚠️ The main
   v1 PII channel.
   - Mitigation: donation context lives only in **private, staff-only
     annotations** (never public); the prompt warns against entering donor
     identity; and a Super Admin can **redact** the text via the audited
     PII-erasure path (§3). Even before redaction, exposure is limited to staff.
2. **A donor's name reaching a *public* field.** Structurally closed: donations
   have **no public free text**, and expense usage descriptions concern spending
   (vendors/purpose), not donors (BR-P2).
3. **Receipts revealing a sender's name.** Removed from v1 entirely — **receipts
   are a Version 2 feature** (see [`ROADMAP.md`](./ROADMAP.md)). This deliberately
   eliminates the file-based leak vector from the first release.
4. **Future bank/payment imports carrying the payer's identity.** *(Post-v1.)*
   The integration adapter **strips donor-identifying fields before persistence**;
   only amount, timestamp, provider, and provider txn id are retained. See §5 and
   [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md).

---

## 2. Public vs private information

The system enforces an explicit split (BR-P; [`BUSINESS_RULES.md`](./BUSINESS_RULES.md) §7):

- **Public:** reports, statistics, balance, the donation account, and expense
  **usage descriptions**.
- **Private (staff-only):** annotations, reversal reasons, audit logs, staff
  identities.
- **Nonexistent:** donor identity.

Because donations have no public text, no public surface can leak donor identity.
Statistics and reports are aggregates only — there is no per-donor dimension to
expose because none exists.

---

## 3. PII-erasure exception (privacy outranks immutability)

The ledger is append-only, but **privacy is a higher principle than immutability**.
If donor identity is accidentally entered into free text, it must be removable.

- A Super Admin with `pii.erase` may **redact** the offending text — an annotation
  or a reversal-reason annotation (the only free-text in the system).
- Redaction **overwrites** the content with a tombstone, genuinely removing the
  identity from the database (not merely hiding it) (BR-X2).
- It is **narrow**: only free text, **never** financial fields (amounts, dates,
  category), which stay strictly immutable (BR-X3).
- It is **audited** — recording who/when/which record, **without** copying the
  leaked text into the audit entry (BR-X4). This is why the audit log never
  duplicates reversal-reason text.
- This is the single, deliberate exception to append-only content
  (ADR-0009).

---

## 4. Data integrity controls & the restore threat

### 4.1 Immutable ledger
- Append-only with reversal-only corrections — no role, including Super Admin, can
  edit or delete financial history (invariant I2). A reversal's amount is
  **derived from its target**, so it cannot cancel a different amount (I3).
- **DB-level enforcement** (defense in depth, per the mutability matrix in
  [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) §2, §11): triggers reject
  `UPDATE`/`DELETE` on strictly append-only tables (`ledger_entries`,
  `audit_logs`, `settings_history`, `donation_accounts`); the application connects
  with a **least-privilege DB role** that lacks `UPDATE`/`DELETE` on them.
- **Atomic writes**: entry + audit in one transaction (BR-C1).
- **Idempotent reversals**: `UNIQUE(reverses_entry_id)` prevents double reversal.

### 4.2 The admin/restore threat (⚠️ addressed)
The higher-privilege threat is not a treasurer but a **Super Admin (or a host
operator) using a database restore to rewrite history** — a restore can silently
revert or erase ledger entries and even wipe the in-database audit log, bypassing
every in-app immutability control.

Controls:
- **Restore is not an in-bot action.** It is an **operator-only host procedure**,
  exceptional, and reserved for disaster recovery (see
  [`DEPLOYMENT.md`](./DEPLOYMENT.md)). There is no "restore" button.
- **Off-box audit of restores.** Because an in-DB audit entry could itself be wiped
  by a restore, every restore is recorded to an **off-box** log (host/operator
  records) with who/when/why (BR-AU5).
- **Governance resilience.** Running with **≥2 Super Admins** (recommended) and a
  documented break-glass recovery reduces the "single unchecked admin" risk
  ([`USER_ROLES.md`](./USER_ROLES.md) §5).
- **Backups off-box.** Backups and the backup encryption key are kept off the VPS
  so an attacker who takes the host cannot both restore-tamper and control the
  archive (§8, [`DEPLOYMENT.md`](./DEPLOYMENT.md)).

> Residual risk: a determined operator with full host access is ultimately trusted
> infrastructure; the controls make tampering **detectable and accountable**, not
> impossible. This is an honest limitation, documented rather than hidden.

---

## 5. Future integrations & PII *(post-v1)*

When automatic bank/payment integration arrives:

- Raw provider payloads are stored in `external_transactions.raw_payload` **only
  after donor-identifying fields are removed**. The adapter screens before
  persistence.
- Reconciliation links an external transaction to a ledger donation by **amount +
  time + provider txn id** — never by payer identity. Automatic donations are
  authored by the **system actor** (BR-SY).
- Idempotency (`UNIQUE(provider, provider_txn_id)`) prevents double-counting on
  webhook re-delivery.
- Provider webhooks must be **authenticated** (signature/secret verification) over
  TLS. See [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md).

---

## 6. Authentication & authorization

- **Identification** = the caller's Telegram ID, matched against `staff_users`.
- **Authorization** = permission checks in the **application layer** (not in
  handlers), so every current and future adapter enforces the same rules
  (see [`USER_ROLES.md`](./USER_ROLES.md)).
- **First Super Admin** is bootstrapped from an environment variable
  (`FIRST_SUPER_ADMIN_TELEGRAM_ID`); thereafter only `user.manage` holders create
  staff. No self-service signup exists. The same idempotent seed is the
  **break-glass recovery** path.
- **System actor** is a non-login principal for machine actions; it cannot be used
  by a person (BR-SY).
- **Deactivation** revokes access immediately; audit history is preserved.
- **Least privilege UI**: users see only permitted actions, but the server always
  re-verifies.

---

## 7. Secrets & configuration

- All secrets (bot token, DB credentials, backup encryption key, future provider
  keys) come from the environment / a secrets manager — **never** committed to the
  repo. `.env` is git-ignored; `.env.example` documents keys with placeholders.
- The bot token is treated as highly sensitive (full control of the bot); rotate
  if leaked and keep it out of logs.
- Config is loaded once into a typed object; nothing else reads env vars directly.
- See [`CONFIGURATION.md`](./CONFIGURATION.md).

---

## 8. Transport, platform & backups

- Telegram traffic is TLS-encrypted by the platform. Prefer **webhook mode behind
  HTTPS** (valid certificate) in production, or long polling if webhooks are not
  feasible; either way no inbound plaintext.
- The VPS exposes only what is necessary (reverse proxy / firewall); the database
  is **not** publicly reachable. See [`DEPLOYMENT.md`](./DEPLOYMENT.md).
- Backups are **encrypted at rest**, access-restricted, and **replicated off the
  VPS**. The **encryption key is stored separately from the backups** so a single
  host compromise does not yield both.

---

## 9. Logging & observability

- **Never log** donor identifiers. For public users, do not log the Telegram ID at
  all; use a transient, non-persistent correlation id.
- **Never log** private free text (annotation / reversal-reason content).
- Structured logs capture actions and errors without PII.
- Audit logs (in-DB) are the authoritative record of privileged actions and are
  append-only; restore events are additionally logged off-box (§4.2).

---

## 10. Legal note (staff PII)

The system processes limited **staff** personal data (Telegram ID, optional
display name) for authorization and audit — not donor data. This should be handled
consistent with Uzbekistan's personal-data legislation: collect the minimum,
restrict access to Super Admins, retain only while a person is an operator (or as
required for audit integrity), and disclose the purpose to staff during
onboarding. No donor personal data is processed at all.

---

## 11. Threat model (summary)

| Threat | Impact | Primary mitigation |
|--------|--------|--------------------|
| Donor de-anonymization via records | Breaks core promise | No capability to store donor identity; no public donation free text (structural) |
| Donor identity typed into a note | Privacy breach | Notes are private (staff-only) + audited PII-erasure/redaction |
| **Admin/operator rewrites history via restore** | **Breaks trust model** | **Restore is operator-only, exceptional, off-box audited; ≥2 admins; off-box backups** |
| Treasurer falsifying history | Loss of trust | Immutable ledger + reversal-only + derived reversal amount + audit + DB triggers |
| Unauthorized privileged action | Fraud/tampering | Permission checks in app layer; least-privilege; audit |
| Compromised/lost sole admin | Governance lockout / abuse | ≥2 admins recommended; break-glass re-seed |
| Stolen bot token | Full bot takeover | Secret hygiene, rotation, no token in logs |
| DB exposed to internet | Data/integrity risk | Private network, firewall, least-privilege DB role |
| Backup theft | Exposure of staff/audit data | Encrypted, access-restricted, off-box backups; separate key |
| Donor identity via receipt image | Privacy breach | **Removed from v1** (receipts = V2) |
| Donor identity via bank payload *(post-v1)* | Privacy breach | Strip identifying fields before persistence |
| Webhook spoofing *(post-v1)* | Fake donations | Signature/secret verification + idempotency |
| Replay of bank webhook *(post-v1)* | Double counting | `UNIQUE(provider, provider_txn_id)` |
| Public report query flooding | Availability/cost | Best-effort rate limiting (see §12); PostgreSQL handles expected load |

> Note: even in the worst-case full breach, **donor anonymity holds**, because
> donor identity is never present in the system.

---

## 12. Open items to revisit

- Automated PII scanning on annotation text (a future enhancement to reduce human
  error before redaction is ever needed).
- Best-effort **rate limiting** on public report/statistics queries as a light DoS
  guard (not a v1 blocker; PostgreSQL comfortably handles the expected workload —
  report **caching** is explicitly a future optimization, not v1).
- Receipt handling and redaction policy — designed at the start of **Version 2**.
- Formal data-retention statement for staff PII and audit/ledger (currently:
  ledger/audit retained indefinitely for transparency; staff PII per §10).
