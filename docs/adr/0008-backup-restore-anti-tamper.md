# ADR-0008 — Backup/Restore Anti-Tamper (restore is operator-only)

**Status:** Accepted — 2026-07-09 (from Phase 2.5 review)

## Context
The immutable ledger (ADR-0002) protects against a treasurer editing history, but
the Phase 2.5 review found a bigger hole: a **database restore** can silently
revert or erase ledger entries and even wipe the in-database audit log, bypassing
every in-app immutability control. The higher-privilege threat is a Super Admin or
host operator, not a treasurer. The original design exposed restore as an in-bot
`backup.manage` action.

## Decision
- **Restore is removed from the bot.** There is no restore button, use case, or
  permission. It is an **operator-only host procedure**, exceptional and reserved
  for disaster recovery (see [`DEPLOYMENT.md`](../DEPLOYMENT.md) §6).
- `backup.manage` covers only **creating and downloading** backups.
- **Off-box audit of restores:** because an in-DB audit entry can itself be wiped
  by a restore, every restore is recorded to an **off-box** log by the operator
  (who/when/why/which backup) (BR-AU5).
- **Off-box backups + separate key:** backups are replicated off the VPS and the
  encryption key is stored separately, so one host compromise yields neither a lone
  copy of history nor the means to forge one.
- **Governance resilience:** recommend **≥2 Super Admins** and a documented
  break-glass recovery ([`USER_ROLES.md`](../USER_ROLES.md) §5).

## Consequences
- ✅ Tampering via restore becomes **detectable and accountable**, not a one-tap
  action.
- ✅ History survives loss of the VPS (off-box copies).
- ➖ Restore is less convenient (host access + runbook) — intentional for such a
  destructive operation.
- ➖ Honest residual risk: an operator with full host access is ultimately trusted
  infrastructure; controls make abuse visible, not impossible. Documented, not
  hidden.

See [`SECURITY.md`](../SECURITY.md) §4 and [`DEPLOYMENT.md`](../DEPLOYMENT.md) §5–6.
