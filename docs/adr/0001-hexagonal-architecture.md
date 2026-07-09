# ADR-0001 — Hexagonal (Ports & Adapters) Architecture

**Status:** Accepted — 2026-07-09

## Context
The product is Telegram-first, but the owner explicitly wants future expansion
(web panel, public API, automatic bank/payment integrations) **without rewriting
business logic**. A design centered on the Telegram framework would couple
business rules to aiogram and make every future channel a rewrite. The project is
also meant to be maintainable for many years and easily testable.

## Decision
Adopt **hexagonal architecture (ports & adapters)** with clean-architecture
layering:
- A **domain** layer of pure business rules (no framework, no I/O).
- An **application** layer of use cases that orchestrate the domain and define
  **ports** (interfaces) for everything external.
- **Adapters** implement those ports: Telegram (aiogram), persistence
  (SQLAlchemy/PostgreSQL), file storage, scheduler, and — later — bank gateways
  and a web/API front end.
- A **composition root** wires concrete adapters to the core.
Dependencies point inward only. Authorization and transactions live in the
application layer so every adapter enforces identical rules.

## Consequences
- ✅ Telegram is replaceable; new channels/integrations are additive adapters.
- ✅ The bulk of logic is unit-testable with no Telegram and no database.
- ✅ Clear boundaries aid long-term maintainability and onboarding.
- ➖ More upfront structure and indirection than a "handlers-call-the-DB" script.
- ➖ Requires discipline: no business logic in handlers, no framework imports in
  the core. Enforced by review and tests.

See [`PROJECT_ARCHITECTURE.md`](../PROJECT_ARCHITECTURE.md).
