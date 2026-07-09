# API & Payment Integrations (Future)

> **Last updated:** 2026-07-09
> **Status: designed-for, NOT built in v1.** This document describes how automatic
> bank/payment integrations attach to the system without rewriting business logic.
> v1 works fully manually (treasurers record donations). Terms in
> [`GLOSSARY.md`](./GLOSSARY.md).

---

## 1. Goal

Allow donations to be created **automatically** from Uzbek payment providers and
bank APIs (Click, Payme, Uzcard, Humo, and bank statement/webhook APIs) while
preserving every core rule:

- Donor anonymity (invariant I1) — even though providers know the payer.
- Immutable ledger (invariant I2) — automatic donations obey the same rules.
- Reproducible reports — automatic and manual donations live in one ledger.

---

## 2. Where it plugs in (architecture)

Integrations are **outbound adapters** plus a thin **inbound adapter** for
webhooks; they feed the *existing* `RecordDonation` use case. The core does not
change. (See [`PROJECT_ARCHITECTURE.md`](./PROJECT_ARCHITECTURE.md) §8.)

```
Provider (Click/Payme/…)
   │  webhook / API poll
   ▼
Inbound integration adapter  ──►  screens payload (strip PII)
   │                                 │
   │                                 ▼
   │                       external_transactions (raw, idempotent)
   │                                 │  reconciliation
   ▼                                 ▼
 BankGateway (outbound port)   RecordDonation use case  ──►  ledger_entries
                                     │
                                     ▼
                               audit_logs
```

Key building blocks already designed in v1's schema:
- `ledger_entries.source = 'bank_api'` distinguishes automatic donations.
- Automatic donations are authored by the reserved **system actor** (BR-SY), so
  `recorded_by` is always defined even without a human recorder.
- `external_transactions` stores raw provider events, idempotently.
- `external_transactions.matched_entry_id` links a raw event to its donation.

---

## 3. Idempotency (no double counting)

- `external_transactions` has `UNIQUE(provider, provider_txn_id)`.
- Webhooks are frequently re-delivered; the unique key guarantees the same
  provider event **never** creates a second donation (BR-C3).
- Processing is: `INSERT ... ON CONFLICT DO NOTHING` → if newly inserted and
  valid, create the donation via `RecordDonation`; else ignore.

---

## 4. Reconciliation model

Two modes, both supported by the same tables:

1. **Auto-create (provider-confirmed payments):** for Click/Payme-style flows
   where the provider confirms a completed payment, the adapter creates the
   donation immediately (`source='bank_api'`) and sets `status='matched'`.
2. **Import-then-match (bank statements):** raw bank transactions are imported
   with `status='imported'`; a treasurer or an auto-matcher links them to
   donations (by amount + time), producing ledger entries and setting
   `status='matched'`. Unmatched items stay visible for review; irrelevant ones
   are marked `ignored`.

Either way, **the ledger remains the single source of truth**; external
transactions are an auditable staging area, not the balance.

---

## 5. Privacy screening (mandatory)

⚠️ Provider payloads typically contain the payer's name, card mask, phone, etc.
Before **any** persistence:

- The adapter extracts **only**: amount, currency, timestamp, provider,
  `provider_txn_id`, and a status.
- All donor-identifying fields are **dropped** and never written to
  `raw_payload`. `raw_payload` stores only the screened, non-identifying subset.
- This keeps invariant I1 intact even with real payment rails.
  See [`SECURITY.md`](./SECURITY.md) §5.

> If a provider makes it impossible to receive an event without identity, the
> identity is discarded in-memory immediately after extracting the amount; it is
> never logged or stored.

---

## 6. Webhook security

- Serve webhooks over HTTPS behind the reverse proxy.
- **Verify authenticity** of every provider callback (HMAC signature / shared
  secret / IP allowlist, per provider).
- Reject unverified or malformed callbacks; log the rejection without PII.
- Respond quickly and process asynchronously to avoid provider timeouts/retries
  compounding.

---

## 7. Payment initiation (optional, later)

A future "donate in-bot" experience (e.g., a Click/Payme payment link or invoice
inside Telegram) is possible:

- The bot would present a payment link/invoice; the provider handles the actual
  payment and returns a confirmation webhook, which flows through §2–§6.
- Even here, the bot stores **no** donor identity — only the resulting donation
  amount. The provider (not us) holds the payer relationship.
- Telegram's native payments API could be evaluated, but it may attach buyer info
  to the bot; if adopted, the same screening rule (§5) applies before persistence.

---

## 8. Provider abstraction

Define a single outbound port so providers are interchangeable:

```
BankGateway (port)
  - verify_callback(request) -> VerifiedEvent | Rejected
  - normalize(event) -> NormalizedDonationEvent   # amount, ts, provider_txn_id
```

Each provider (Click, Payme, Uzcard, Humo, bank X) is a separate adapter
implementing this port. Adding a provider = new adapter + config keys
(`CLICK_*`, `PAYME_*`, …), **no** change to the core or the ledger.

---

## 9. Rollout plan (high level)

1. Ship v1 fully manual (no integrations).
2. Add `external_transactions` handling + one provider (whichever the org uses
   most) behind a feature flag.
3. Add reconciliation UI/flow for treasurers.
4. Add remaining providers as adapters.
5. (Optional) In-bot payment initiation.

Tracked in [`ROADMAP.md`](./ROADMAP.md). Each provider integration gets its own
ADR capturing provider-specific decisions.
