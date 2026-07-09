# Anonymous Donation Management Telegram Bot

> **Status: Design phase (Phase 2.5 complete — documentation).** No implementation
> code yet. This repository is being repurposed as a **fresh project**; any
> previous (warehouse) code is legacy and will be archived/removed at the start of
> implementation (Phase 3), only after documentation is approved.

A **Telegram-first** bot for managing donations to a single organization in
Uzbekistan, built on two principles that guide every decision:

- 🔒 **Privacy** — the system **never** stores donor identity.
- 🔍 **Transparency** — every figure shown is **derived from an immutable ledger**
  and independently reproducible.

When privacy and transparency conflict, **privacy wins**.

---

## What it does (v1)

- **Anonymous donations** — recorded by treasurers; no donor identity is ever
  captured or stored, and donations carry **no public free text**.
- **Expense tracking** — with a **public usage description** of how money was used.
- **Immutable ledger** — append-only; corrections are **reversals** (whose amount
  is derived from the original); context is added via append-only, private
  **annotations**, never by editing an entry. Every entry has a public
  `#reference_no`.
- **Public reports & statistics** — daily, monthly, yearly, and all-time, derived
  directly from the ledger.
- **Donation account** — the public destination donors send money to.
- **Roles & permissions** — User (public), Treasurer, Super Admin, on a
  permission-based RBAC model.
- **Immutable audit log** — every privileged action, without any donor data.
- **Backups** — scheduled + manual; **restore is an operator-only host procedure**
  (never an in-bot action), off-box audited.
- **Privacy safeguards** — a narrow, audited **PII-erasure** action for leaked
  identity in free text.
- **Uzbek UI** — on a localization layer ready for Russian and English.

**Version 2:** receipts / file attachments (deferred to keep the first release
free of file-based donor-identity risk).

**Designed-for-later (post-v1):** web panel, public API, public anonymized ledger,
report caching, automatic bank/payment integrations (Click, Payme, Uzcard, Humo,
bank APIs), multi-org/campaigns, multi-currency. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Core design decisions

| Decision | Why | Detail |
|----------|-----|--------|
| Hexagonal architecture | Telegram/DB/banks are swappable adapters; core stays pure | [ADR-0001](docs/adr/0001-hexagonal-architecture.md) |
| Immutable, append-only ledger | Trustworthy, reproducible financial history | [ADR-0002](docs/adr/0002-immutable-ledger.md) |
| Money as integer minor units (tiyin) | Exact math, no float drift | [ADR-0003](docs/adr/0003-money-integer-minor-units.md) |
| Structural donor anonymity | No capability to store donor identity | [ADR-0004](docs/adr/0004-anonymity-boundary.md) |
| Permission-based RBAC | New roles without code changes | [ADR-0005](docs/adr/0005-permission-based-rbac.md) |
| aiogram 3.x · Python 3.13 · PostgreSQL | Async, production-grade, maintainable | [ADR-0006](docs/adr/0006-aiogram-and-stack.md) |
| Reports derived from the ledger | Verifiable, reproducible numbers | [ADR-0007](docs/adr/0007-reports-derived-from-ledger.md) |
| Backup/restore anti-tamper | Restore is operator-only, off-box audited | [ADR-0008](docs/adr/0008-backup-restore-anti-tamper.md) |
| Public/private split + PII-erasure | Privacy outranks immutability for free text | [ADR-0009](docs/adr/0009-public-private-and-pii-erasure.md) |
| Annotations + derived reversal | Context without editing; reversals can't invent amounts | [ADR-0010](docs/adr/0010-annotations-and-derived-reversal.md) |
| System actor | Defined author for machine actions | [ADR-0011](docs/adr/0011-system-actor.md) |

---

## Documentation (single source of truth)

Read in this order:

1. [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — vision, scope, principles
2. [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — precise domain vocabulary
3. [`docs/USER_ROLES.md`](docs/USER_ROLES.md) — roles, permissions, onboarding
4. [`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md) — ledger, corrections, money, reports
5. [`docs/PROJECT_ARCHITECTURE.md`](docs/PROJECT_ARCHITECTURE.md) — hexagonal layers & structure
6. [`docs/DATABASE_DESIGN.md`](docs/DATABASE_DESIGN.md) — schema, mutability matrix & constraints
7. [`docs/BOT_FLOW.md`](docs/BOT_FLOW.md) — Telegram flows per role
8. [`docs/SECURITY.md`](docs/SECURITY.md) — privacy model & threat model
9. [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) — env vars & runtime settings
10. [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Docker/VPS, backups, operator-only restore
11. [`docs/API_INTEGRATIONS.md`](docs/API_INTEGRATIONS.md) — future bank/payment design
12. [`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md) — how correctness is guaranteed
13. [`docs/ROADMAP.md`](docs/ROADMAP.md) — phased delivery plan
14. [`docs/adr/`](docs/adr/) — Architecture Decision Records (the *why*)

---

## The invariants (never violated)

| # | Invariant |
|---|-----------|
| I1 | No donation record can hold any donor identifier; donations have no public free text. |
| I2 | Ledger entries are never updated or deleted — by anyone. |
| I3 | Corrections are reversals; each entry is reversible at most once; a reversal's amount is derived from the original. |
| I4 | Money is integer minor units; never a float. |
| I5 | Every reported number is derived from the ledger. |
| I6 | Every privileged action is audited; restore is additionally logged off-box. |
| I7 | Donor-context free text lives only in private, staff-only annotations and is PII-redactable; nothing donor-related is ever public. |
| I8 | Reports bucket time in the org time zone; storage is UTC. |

---

## Development phases

- **Phase 1 — Analysis** ✅
- **Phase 2 — Documentation** ✅
- **Phase 2.5 — Architecture review** ✅ *(all approved Critical + High issues
  resolved; this repository's current state)*
- **Phase 3 — Implementation** — module by module, after documentation is
  approved. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

> No implementation begins until this documentation is reviewed and approved.
> The documentation is the single source of truth; code must follow it, and any
> change to a decision is reflected here (with an ADR) before or alongside the
> code.
