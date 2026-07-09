# Roadmap

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Phased delivery plan. Phase 1 (analysis), Phase 2 (documentation), and
> Phase 2.5 (architecture review) precede any code. Implementation is **module by
> module**, each fully working before the next. Dates are intentionally omitted;
> sequence and gates matter more than calendar.

---

## Phase 1 — Analysis ✅
- Requirements clarified, design tensions resolved, decisions agreed.

## Phase 2 — Documentation ✅
- All design documents written.

## Phase 2.5 — Architecture review ✅
- Independent critical review; all approved Critical + High issues resolved in the
  docs (immutable-ledger consistency, mutability matrix, annotations, derived
  reversals, system actor, public/private split, PII-erasure, backup/restore
  anti-tamper). Scope trimmed: **receipts → V2**, **no report caching in v1**,
  **no public ledger in v1**.
- **Gate:** documentation approved by the project owner before any code.

## Phase 3 — Implementation (module by module)

Each milestone ends with tests (per [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md))
and updated docs/ADRs where needed.

### M0 — Project skeleton & foundations
- Repo/package layout (`src/donation_bot/...`), tooling, `pyproject`, linting.
- Config loader (typed, fail-fast), logging (PII-safe), i18n scaffold (uz).
- Docker + compose, PostgreSQL, Alembic baseline.
- Composition root / DI wiring.
- **Decide & execute** archival/removal of the legacy warehouse code (only after
  documentation approval — see repository policy).

### M1 — Domain core
- `Money`/`Currency` value objects; `Period`/time helpers (org timezone).
- Ledger entities and invariants (immutability, **reversal effect derived from the
  target**, "reversed" computed); annotation + redaction rule.
- Access model: `StaffUser` (incl. **system actor**), `Role`, `Permission`,
  permission resolution.
- Pure unit tests for all invariants (I1–I8 relevant parts).

### M2 — Persistence & access control
- SQLAlchemy models + repositories implementing the ports.
- Alembic migrations for the full v1 schema + append-only triggers +
  `entry_annotations` redaction-only trigger + **two DB roles** per the privilege
  matrix.
- Seed: roles, permissions, mapping, **system actor**, expense categories, default
  settings (incl. amount limits, backdate window), **first Super Admin** from env.
- Integration tests proving the mutability matrix and constraints.

### M3 — Ledger & annotation use cases
- `RecordDonation`, `RecordExpense`, `ReverseEntry` (derived amount),
  `AddAnnotation` with permissions + atomic audit writes; `reference_no` assignment.
- Balance computation via `ledger_effective`.

### M4 — Reporting & statistics
- `GenerateReport` (day/month/year/all-time/custom), `GetStatistics` — all derived
  directly from the ledger in PostgreSQL (no caching); timezone-correct;
  reproducibility tests. Public output includes expense usage descriptions, never
  private text.

### M5 — Telegram adapter (public + treasurer)
- aiogram 3 wiring (polling for dev), menus, FSM flows for public viewing and
  treasurer recording / reversal / private annotation, localized (uz).
- Large-amount and back-date confirmations; `#reference_no` in confirmations.
- **No receipts** (V2).

### M6 — Super Admin governance
- Manage staff/roles, **manage expense categories**, settings, donation account
  (true append-only), audit log viewer, and **PII-erasure (RedactAnnotation)**.

### M7 — Backups & operations
- Scheduled + manual backups (encrypted, **off-box** copy, key stored separately),
  missed-run catch-up, health checks.
- **Restore runbook** (operator-only host procedure, off-box audited — not in the
  bot).
- Webhook mode + reverse proxy for production; hardening checklist satisfied.

### M8 — Production launch (v1)
- Staging validation, **test-restore** verified, monitoring/alerts on, ≥2 Super
  Admins configured.
- **Gate:** anonymity, immutability, and public/private guard tests green;
  hardening checklist done.

---

## Version 2 (next major version)

- **Receipts / attachments:** upload, default-sensitive classification, access
  control, external storage, PII-erasure for files, and the associated
  permissions (`receipt.attach`, `receipt.view_sensitive`). Deferred from v1 to
  keep the first release free of file-based donor-identity risk.

---

## Phase 4 — Post-v1 enhancements (designed-for, not committed)

Prioritized as the organization needs them:

1. **Scheduled public report posting** to a channel/group.
2. **Localization:** add Russian, then English catalogs.
3. **Public anonymized per-entry ledger** (transparency enhancement over the
   `ledger_effective` read model).
4. **Report caching / materialized summaries** — only if load ever warrants it
   (still derived from the ledger).
5. **First payment integration** (the provider the org uses most) via an adapter +
   `external_transactions` + reconciliation, authored by the system actor (see
   [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md)). Feature-flagged.
6. **Remaining providers** (Click / Payme / Uzcard / Humo / bank APIs) as adapters.
7. **In-bot donation initiation** (payment links/invoices), if desired.
8. **Web admin panel** and/or **public REST API** as new inbound adapters.
9. **Multi-org / campaigns / multi-currency** (scope added to entities &
   permissions; `currency` field already present).
10. **Automated PII scanning** on annotation text (reduce reliance on manual
    redaction).

Each item is a self-contained adapter/feature that plugs into the existing core
without rewriting business logic — the whole point of the architecture.

---

## Guiding rules for delivery

- Never merge a module without its invariant tests.
- Keep migrations additive/backward-compatible where possible.
- Update this documentation set (and add an ADR) whenever a decision changes —
  the docs remain the single source of truth.
- Prefer finishing one working module over starting several half-done ones.
- Prefer the simpler solution when it provides the same long-term maintainability.
