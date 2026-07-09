# Architecture Decision Records (ADR)

> **Last updated:** 2026-07-09

An **ADR** captures a single significant decision: its context, the choice made,
and the consequences. ADRs are **immutable** once accepted — if a decision
changes, add a *new* ADR that supersedes the old one (never rewrite history). This
mirrors the project's own immutable-ledger philosophy.

## Why we keep ADRs
This project is meant to live for many years. New engineers must be able to
understand **why** the system is the way it is, not just *what* it does. ADRs are
the durable record of that reasoning.

## Format
Each ADR uses:
- **Status** — Proposed | Accepted | Superseded by ADR-XXXX
- **Context** — the forces and constraints at play
- **Decision** — what we chose
- **Consequences** — trade-offs, what becomes easy/hard

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./0001-hexagonal-architecture.md) | Hexagonal (ports & adapters) architecture | Accepted |
| [0002](./0002-immutable-ledger.md) | Immutable, append-only ledger with reversal-only corrections | Accepted |
| [0003](./0003-money-integer-minor-units.md) | Money as integer minor units (tiyin) | Accepted |
| [0004](./0004-anonymity-boundary.md) | Structural donor-anonymity boundary | Accepted |
| [0005](./0005-permission-based-rbac.md) | Permission-based RBAC with role presets | Accepted |
| [0006](./0006-aiogram-and-stack.md) | aiogram 3.x, Python 3.13, PostgreSQL stack | Accepted |
| [0007](./0007-reports-derived-from-ledger.md) | Reports derived from the ledger | Accepted |
| [0008](./0008-backup-restore-anti-tamper.md) | Backup/restore anti-tamper (restore is operator-only) | Accepted |
| [0009](./0009-public-private-and-pii-erasure.md) | Public/private data split & PII-erasure exception | Accepted |
| [0010](./0010-annotations-and-derived-reversal.md) | Annotations for context & derived reversal amounts (refines 0002) | Accepted |
| [0011](./0011-system-actor.md) | System actor for machine-initiated actions | Accepted |

> ADRs 0008–0011 were added in the **Phase 2.5 architecture review**. They refine
> (do not overturn) the originals: 0010 refines 0002; 0009 refines 0004. Note also
> a scope decision from that review — **receipts are deferred to Version 2** (see
> [`ROADMAP.md`](../ROADMAP.md)); no ADR reverses this, it is a scope choice.

## Adding a new ADR
1. Copy the format above into `NNNN-short-title.md` (next number).
2. Fill in Context / Decision / Consequences.
3. Link it in this index; if it supersedes another, update the old ADR's status.
