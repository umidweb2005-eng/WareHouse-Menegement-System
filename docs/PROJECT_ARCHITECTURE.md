# Project Architecture

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Style: **Hexagonal (Ports & Adapters)** + Clean Architecture layering.
> Terms in [`GLOSSARY.md`](./GLOSSARY.md); decisions in [`adr/`](./adr/).
> **Simplicity note:** we use these boundaries because they buy real long-term
> maintainability (swappable Telegram, additive bank integrations, testable core),
> not architecture for its own sake. Where a simpler shape serves equally well, we
> take it.

---

## 1. Goals this architecture serves

1. **Telegram is replaceable.** Business rules must not depend on aiogram. A web
   panel or REST API can be added later as *another adapter* over the same core.
2. **Bank integrations are additive.** Click/Payme/Uzcard/Humo/bank APIs plug in
   as adapters without touching domain logic *(post-v1)*.
3. **Testable core.** Domain and application logic run in tests with no Telegram
   and no real database.
4. **Longevity.** Clear boundaries and explicit contracts so the system stays
   understandable for years.

---

## 2. The layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADAPTERS (outside)                        │
│                                                                   │
│   Inbound (drivers)                    Outbound (driven)          │
│   ┌────────────────┐                   ┌───────────────────────┐  │
│   │ Telegram bot   │                   │ PostgreSQL repos      │  │
│   │ (aiogram 3.x)  │                   │ (SQLAlchemy)          │  │
│   ├────────────────┤                   ├───────────────────────┤  │
│   │ Scheduler      │                   │ Backup service        │  │
│   │ (backups)      │                   ├───────────────────────┤  │
│   │                │                   │ Clock / UUID / etc.   │  │
│   ├────────────────┤                   ├───────────────────────┤  │
│   │ (future) Web   │                   │ (future) Bank APIs    │  │
│   │ (future) REST  │                   │ (future) File storage │  │
│   │                │                   │ (future) Notifier     │  │
│   └───────┬────────┘                   └───────────▲───────────┘  │
│           │ calls use cases                        │ implements    │
│           │ (inbound ports)              outbound ports (interfaces)│
└───────────┼────────────────────────────────────────┼──────────────┘
            ▼                                          │
┌───────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER (use cases)                   │
│   RecordDonation · RecordExpense · ReverseEntry · AddAnnotation     │
│   RedactAnnotation · GenerateReport · GetStatistics ·               │
│   GetActiveDonationAccount · ManageStaff · AssignRole ·             │
│   ManageCategory · ConfigureDonationAccount · UpdateSetting ·       │
│   QueryAuditLog · RunBackup · ListBackups                           │
│   - orchestrates domain objects                                     │
│   - enforces permissions                                            │
│   - defines ports (repository/clock interfaces)                     │
│   - owns transactions (Unit of Work)                                │
└───────────────────────────────┬───────────────────────────────────┘
                                 ▼
┌───────────────────────────────────────────────────────────────────┐
│                          DOMAIN LAYER (core)                        │
│   Entities: LedgerEntry (donation/expense/reversal), Annotation,    │
│             StaffUser, Role, Permission, DonationAccount            │
│   Value objects: Money, Currency, Period, PermissionCode, Reference │
│   Domain services & invariants (immutability, derived reversal, RBAC)│
│   Pure Python. No aiogram, no SQL, no I/O.                          │
└───────────────────────────────────────────────────────────────────┘
```

**Dependency rule:** dependencies point **inward only**. Domain knows nothing of
the application layer; the application layer knows nothing of adapters. Adapters
depend on the core through interfaces (ports). Restore is deliberately **not** a
use case — it is an operator-only host procedure ([`DEPLOYMENT.md`](./DEPLOYMENT.md)).

---

## 3. Ports (contracts owned by the core)

**Inbound ports** — what the core offers (invoked by adapters):
- Each **use case** is an inbound port (e.g., `RecordDonation.execute(command)`).
  The v1 use cases are listed in the layer diagram above and traced to flows in
  [`BOT_FLOW.md`](./BOT_FLOW.md) §9.

**Outbound ports** — what the core needs (implemented by adapters):
- `LedgerRepository` (append donations/expenses/reversals) and `LedgerReadModel`
  (the derived `ledger_effective` view: balances, reports, statistics)
- `AnnotationRepository` (append notes/reversal reasons; redact)
- `StaffRepository`, `RoleRepository`, `PermissionResolver`
- `CategoryRepository`
- `DonationAccountRepository`
- `SettingsRepository`
- `AuditLogRepository`
- `Clock`, `IdGenerator`
- `UnitOfWork` (transaction boundary)
- `BackupService` (create/list backups)
- **Version 2:** `AttachmentStorage` (receipts) — *not implemented in v1*
- **Post-v1:** `ExternalTransactionRepository`, `BankGateway`, `Notifier`

Adapters provide concrete implementations; the **composition root** wires them.

---

## 4. Request lifecycle (example: recording a donation)

```
Treasurer taps "Add donation" in Telegram
        │
Telegram adapter (aiogram handler + FSM)
        │  collects amount, date (event_at), source, optional PRIVATE note
        │  resolves caller Telegram ID → StaffUser + permissions
        ▼
Application: RecordDonation use case
        │  1. check permission `donation.record`
        │  2. validate amount (BR-M) & event_at bounds (BR-L7)
        │  3. build LedgerEntry (Money value object, invariants)
        │  4. within UnitOfWork:
        │        - LedgerRepository.add(entry)            → reference_no assigned
        │        - AnnotationRepository.add(note)         (only if provided; private)
        │        - AuditLogRepository.add(audit entry)
        ▼
Adapters: SQLAlchemy repos persist to PostgreSQL (one transaction)
        │
        ▼
Telegram adapter formats confirmation "…Reference: #<reference_no>" (Uzbek) → replies
```

The use case never imports aiogram or SQLAlchemy. The handler never contains
business rules. Machine-initiated writes (scheduled backup; future auto-imports)
run the same use cases authored by the **system actor**.

---

## 5. Proposed source layout

```
donation-bot/
├── src/
│   └── donation_bot/
│       ├── domain/                  # pure core
│       │   ├── ledger/              # LedgerEntry, reversal derivation, rules
│       │   ├── annotations/         # Annotation, redaction rule
│       │   ├── access/              # StaffUser, Role, Permission, system actor
│       │   ├── accounts/            # DonationAccount (append-only)
│       │   ├── money.py             # Money, Currency value objects
│       │   ├── time.py              # Period, org-timezone helpers
│       │   └── events.py            # domain events (future-friendly)
│       │
│       ├── application/             # use cases + ports
│       │   ├── ports/               # repository/clock interfaces
│       │   ├── donations/           # RecordDonation
│       │   ├── expenses/            # RecordExpense, ManageCategory
│       │   ├── ledger/              # ReverseEntry
│       │   ├── annotations/         # AddAnnotation, RedactAnnotation
│       │   ├── reports/             # GenerateReport, GetStatistics
│       │   ├── access/              # ManageStaff, AssignRole, ManageRole, auth
│       │   ├── settings/            # UpdateSetting, ConfigureDonationAccount
│       │   ├── audit/               # QueryAuditLog
│       │   └── backup/             # RunBackup, ListBackups
│       │
│       ├── adapters/                # the outside world
│       │   ├── telegram/            # aiogram: routers, handlers, FSM, keyboards
│       │   ├── persistence/         # SQLAlchemy models, repositories, UoW
│       │   ├── scheduler/           # periodic backups (system actor)
│       │   ├── backup/              # pg_dump/encrypt/off-box replication
│       │   └── external/            # (post-v1) bank/payment gateways
│       │                            # (V2) storage/ for receipts
│       │
│       ├── infrastructure/          # config, db engine, logging, i18n
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── logging.py
│       │   └── i18n/                # translation catalogs (uz; ru/en later)
│       │
│       └── composition/             # dependency injection / wiring
│           └── container.py
│
├── migrations/                      # Alembic (schema + triggers + grants)
├── tests/
│   ├── unit/                        # domain + application (no I/O)
│   ├── integration/                 # repositories against real PostgreSQL
│   └── e2e/                         # bot flows against mocked Telegram
├── docs/                            # this documentation set
├── docker/                          # Dockerfile, compose, entrypoints
├── pyproject.toml
└── .env.example
```

> Note: the `src/donation_bot` package name and layout are the recommended target
> for implementation (Phase 3). The current repository still contains the legacy
> warehouse app; how it is archived/removed is decided at the start of Phase 3
> (repository cleanup happens only after documentation is approved).

---

## 6. Key architectural decisions (see ADRs for full rationale)

| Decision | Summary | ADR |
|----------|---------|-----|
| Hexagonal architecture | Telegram/DB/bank are adapters; core is pure | [ADR-0001](./adr/0001-hexagonal-architecture.md) |
| Immutable ledger | Append-only, reversal-only corrections | [ADR-0002](./adr/0002-immutable-ledger.md) |
| Money as integer minor units | No floats; `Money` value object | [ADR-0003](./adr/0003-money-integer-minor-units.md) |
| No donor identity persisted | Structural guarantee of anonymity | [ADR-0004](./adr/0004-anonymity-boundary.md) |
| Permission-based RBAC | Roles are data, checks use permissions | [ADR-0005](./adr/0005-permission-based-rbac.md) |
| aiogram 3.x · Python 3.13 · PostgreSQL | Async Telegram adapter + stack | [ADR-0006](./adr/0006-aiogram-and-stack.md) |
| Reports derived from ledger | Reproducible, never hand-typed | [ADR-0007](./adr/0007-reports-derived-from-ledger.md) |
| Backup/restore anti-tamper | Restore is operator-only, off-box audited | [ADR-0008](./adr/0008-backup-restore-anti-tamper.md) |
| Public/private split + PII-erasure | Privacy outranks immutability for free text | [ADR-0009](./adr/0009-public-private-and-pii-erasure.md) |
| Annotations + derived reversal | Add context without editing; reversal can't invent amounts | [ADR-0010](./adr/0010-annotations-and-derived-reversal.md) |
| System actor | Defined author for machine actions | [ADR-0011](./adr/0011-system-actor.md) |

---

## 7. Cross-cutting concerns

- **Configuration** — one typed settings object loaded from environment; see
  [`CONFIGURATION.md`](./CONFIGURATION.md). Nothing reads env vars directly except
  the config loader.
- **Localization (i18n)** — all user-facing strings go through the translation
  layer. v1 ships `uz`; `ru`/`en` are added by dropping in catalogs. No hardcoded
  user-facing text in handlers.
- **Logging & observability** — structured logs; **never** log donor identity or
  private free text (annotations/reversal reasons); correlate by request.
  Metrics/health endpoints designed-for.
- **Error handling** — domain raises typed errors; the Telegram adapter maps them
  to friendly localized messages. Unexpected errors never leak internals to users.
- **Time** — a `Clock` port supplies "now"; the org time zone drives report
  bucketing (BR-R4). Storage is UTC.
- **Immutability enforcement** — application logic plus DB triggers and a
  least-privilege DB role realize the **mutability matrix**
  ([`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) §2, §11). Invariants that must not
  race are enforced by DB constraints, not just application checks.
- **Reporting performance** — v1 reads reports directly from PostgreSQL via
  `LedgerReadModel`; **no caching layer** (a documented future optimization —
  [`ROADMAP.md`](./ROADMAP.md)). PostgreSQL comfortably handles the expected load.

---

## 8. How future features plug in (no core rewrite)

| Future feature | Where it attaches |
|----------------|-------------------|
| Receipts (Version 2) | New outbound `AttachmentStorage` adapter + `attachments` table + receipt permissions |
| Web admin panel | New **inbound adapter** calling the same use cases |
| Public REST API | New **inbound adapter** |
| Public anonymized ledger | New read model over `ledger_effective` + a public flow |
| Click/Payme/Uzcard/Humo | New **outbound adapter** (`BankGateway`) + `bank_api` source, feeding `RecordDonation` (authored by the system actor); reconciliation via `ExternalTransactionRepository` |
| Report caching | A materialized/cached `LedgerReadModel` implementation (still derived from the ledger) |
| Multi-currency | Extend `Money`/`Currency`; `currency` field already stored |
| Multi-org / campaigns | Add scope to entities & permissions (anticipated in RBAC) |
| Notifications | New outbound `Notifier` adapter |

See [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md) and [`ROADMAP.md`](./ROADMAP.md).
