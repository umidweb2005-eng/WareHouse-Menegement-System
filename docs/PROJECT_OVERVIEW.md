# Project Overview

> **Status:** Design (Phase 2 / 2.5 — documentation). No implementation yet.
> **Document owner:** Lead Architect
> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)

---

## 1. What we are building

An **anonymous donation management Telegram bot** for a single organization in
Uzbekistan.

The bot lets a community:

- **Donate anonymously** — donations are recorded without ever linking them to a
  donor's identity.
- **See exactly what happened** — every donation received and every expense made
  is visible through transparent, reproducible reports.
- **Be governed** — treasurers record money movements, super admins govern the
  system, and every privileged action is written to an immutable audit log.

The product is **Telegram-first**. There is **no web application** in version 1,
but the system is designed so a web panel, a public REST API, or automatic
bank/payment integrations can be added later **without rewriting the business
logic**.

---

## 2. Why it exists (the problem)

Community and charitable funds live or die by **trust**. Donors want to give
without being named, tracked, or solicited; the community wants proof that money
is handled honestly. These two needs pull in opposite directions:

- Too much record-keeping → donor privacy is violated.
- Too little record-keeping → nobody can verify where the money went.

This project resolves that tension with a deliberate design: **store the money,
never the donor**, and make every stored number **publicly verifiable**.

---

## 3. Guiding principles

These principles are binding. When a design decision is unclear, resolve it in
favor of the principle listed earliest.

1. **Donor privacy is absolute.**
   The system must never persist a donor's name, Telegram ID, username, phone
   number, or any other identifier. No donation record may contain a donor
   reference of any kind. When privacy and transparency conflict, **privacy
   wins** — including a narrow, audited path to erase donor identity that a human
   accidentally entered into free text (see [`SECURITY.md`](./SECURITY.md)).

2. **Transparency by construction.**
   Every figure shown in a report is derived from the underlying ledger, not from
   a manually typed total. Anyone can reproduce the numbers.

3. **Immutable financial history.**
   Donations and expenses are append-only. Financial facts are never edited or
   deleted — by anyone, including Super Admin. Mistakes are fixed with
   **adjustment (reversal) entries**; additional context is added with **append-only
   annotations**, never by editing the original entry.

4. **The core is independent of Telegram.**
   Business rules live in a framework-agnostic core. Telegram is one *adapter*
   plugged into that core, not the center of the system.

5. **Design for years, not for launch day.**
   Favor clarity, explicit contracts, and extensibility over shortcuts. Every
   significant decision is documented (see `adr/`).

6. **Simplicity over cleverness.**
   Version 1 supports one organization and one donation account, works fully
   without any bank integration, and is deliberately small. We add abstractions
   only where they buy real long-term maintainability — not architecture for its
   own sake. The seams for future growth are designed in, but future features are
   not built early.

---

## 4. Actors

| Actor | Identity stored? | Summary |
|-------|------------------|---------|
| **Donor / Public User** | ❌ Never | Interacts with the bot to view reports, statistics, and the donation account. Never creates records. Not persisted. |
| **Treasurer** | ✅ Yes | Records received donations and expenses, writes public expense usage descriptions, and adds optional **private** context notes (annotations). |
| **Super Admin** | ✅ Yes | Governs everything: roles, permissions, settings, the donation account, audit logs, backups; and may perform the narrow, audited PII-erasure action. |
| **System actor** | n/a (reserved, non-login) | A reserved principal used by scheduled jobs and (future) automatic integrations so machine-initiated records have a defined, audited author. See [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md). |

The full permission model is in [`USER_ROLES.md`](./USER_ROLES.md).

> **Key clarification on identity:** Telegram *always* delivers the sender's ID to
> the bot — this cannot be avoided at the protocol level. Our rule is about
> **persistence**: for donors/public users the identity is used transiently to
> reply and then discarded; for treasurers and super admins the Telegram ID is
> stored **because authorization and auditing require it**. See
> [`SECURITY.md`](./SECURITY.md).

---

## 5. Scope

### In scope for v1

- Anonymous donation recording (by treasurers).
- Expense/outflow recording with a **public usage description**.
- Immutable ledger with adjustment (reversal) entries and human-friendly
  **reference numbers**.
- Append-only, **private** annotations for optional staff context on any entry.
- Public reports & statistics: daily, monthly, yearly, and all-time, all derived
  from the ledger (computed directly in PostgreSQL; no caching layer needed at v1
  scale).
- Viewing the configured donation account (e.g., card/account number to donate to).
- Permission-based RBAC with three role presets (User, Treasurer, Super Admin).
- Immutable audit log of every privileged action.
- Scheduled + manual database backups. **Restore is an operator-only host
  procedure** (not an in-bot action) — see [`DEPLOYMENT.md`](./DEPLOYMENT.md).
- A narrow, audited **PII-erasure** action for leaked donor identity in free text.
- Uzbek-language UI, built on a localization layer ready for Russian/English.

### Explicitly out of scope for v1 (designed-for, not built)

- **Receipts / file attachments** — deferred to **Version 2** (removes file-based
  donor-identity leakage risk from the first release).
- **Report caching / materialized summaries** — a future optimization only;
  PostgreSQL handles the expected workload directly.
- **Public anonymized per-entry ledger** — a future transparency enhancement;
  v1 transparency is delivered via reports, statistics, and expense usage
  descriptions.
- Web application / admin panel.
- Public REST API for third parties.
- Automatic bank / payment-provider integration (Click, Payme, Uzcard, Humo,
  bank APIs).
- Multiple organizations, funds, or campaigns.
- Multi-currency.

Each of these has a defined extension point; see
[`PROJECT_ARCHITECTURE.md`](./PROJECT_ARCHITECTURE.md),
[`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md), and [`ROADMAP.md`](./ROADMAP.md).

---

## 6. Technology at a glance

| Concern | Choice | Notes |
|--------|--------|-------|
| Language | Python 3.13+ | |
| Bot framework | aiogram 3.x | Async Telegram adapter only |
| Database | PostgreSQL | Single source of truth |
| Migrations | Alembic | Versioned schema |
| Money | Integer minor units (tiyin) | Never floating point |
| Architecture | Hexagonal (ports & adapters) | Telegram = adapter |
| Deployment | Docker on a VPS | See `DEPLOYMENT.md` |
| Locale (v1) | Uzbek | i18n layer ready for `ru`, `en` |

Rationale for each major choice is recorded as an ADR in [`adr/`](./adr/).

---

## 7. Document map

| Document | Purpose |
|----------|---------|
| [`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md) | This file — vision, scope, principles |
| [`GLOSSARY.md`](./GLOSSARY.md) | Precise definitions of every domain term |
| [`USER_ROLES.md`](./USER_ROLES.md) | RBAC model, permissions, onboarding |
| [`BUSINESS_RULES.md`](./BUSINESS_RULES.md) | Ledger, corrections, money, reporting rules |
| [`PROJECT_ARCHITECTURE.md`](./PROJECT_ARCHITECTURE.md) | Hexagonal layers, ports/adapters, structure |
| [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) | Schema, constraints, ER overview |
| [`BOT_FLOW.md`](./BOT_FLOW.md) | Telegram conversation flows per role |
| [`SECURITY.md`](./SECURITY.md) | Privacy model, threat model, controls |
| [`CONFIGURATION.md`](./CONFIGURATION.md) | Environment variables & settings |
| [`DEPLOYMENT.md`](./DEPLOYMENT.md) | Docker/VPS, backups, restore |
| [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md) | Future bank/payment integration design |
| [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md) | How correctness is guaranteed |
| [`ROADMAP.md`](./ROADMAP.md) | Phased delivery plan |
| [`adr/`](./adr/) | Architecture Decision Records (the *why*) |

> **This documentation is the single source of truth.** Implementation must
> follow it. If reality forces a change, update the relevant document (and add an
> ADR) *before or alongside* the code change.
