# ADR-0006 — Technology Stack: aiogram 3.x, Python 3.13, PostgreSQL

**Status:** Accepted — 2026-07-09

## Context
The system is Telegram-first and must be production-quality and maintainable for
years, with an async, scalable core and a strong relational data model for the
ledger, RBAC, and audit. A stack choice was requested explicitly.

## Decision
- **Language:** Python 3.13+.
- **Telegram framework:** **aiogram 3.x** — modern, async-native, with routers and
  FSM support well-suited to the bot's guided flows. Used strictly as an **inbound
  adapter** (ADR-0001).
- **Database:** **PostgreSQL** — mature relational engine with the constraints,
  triggers, partial unique indexes, and `jsonb` we rely on for immutability and
  auditing.
- **ORM/migrations:** SQLAlchemy (async) + **Alembic** for versioned schema; no
  `create_all` in production.
- **Packaging/tooling:** `pyproject.toml`-based project; linting/formatting/type
  checking configured in Phase 3.
- **Deployment:** Docker on a VPS (see [`DEPLOYMENT.md`](../DEPLOYMENT.md)).

## Consequences
- ✅ Async end-to-end (aiogram + async SQLAlchemy) fits I/O-bound bot workloads.
- ✅ PostgreSQL enforces key invariants at the storage layer (defense in depth).
- ✅ Widely known stack → easier long-term maintenance and hiring.
- ➖ aiogram 3 has a distinct API from 2.x; the team must target 3.x idioms.
- ➖ Async adds concurrency considerations; race-sensitive invariants are enforced
  by DB constraints, not just app logic.
- This is a stack decision, not an architectural one — because Telegram is an
  adapter (ADR-0001), a future move away from aiogram would not touch the core.

Exact library versions are pinned in Phase 3.
