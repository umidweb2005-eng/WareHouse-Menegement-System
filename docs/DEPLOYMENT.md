# Deployment & Operations

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Target: **Docker on a VPS**. This document covers topology, startup,
> migrations, backups, and the operator-only restore procedure. Configuration keys
> are in [`CONFIGURATION.md`](./CONFIGURATION.md).

---

## 1. Topology

```
                Internet (HTTPS)
                     │
             ┌───────▼────────┐
             │ Reverse proxy  │  (Caddy/Nginx/Traefik): TLS, webhook path only
             └───────┬────────┘
                     │  private network
        ┌────────────▼────────────┐   ┌───────────────────┐
        │   bot (app container)    │──▶│  db (PostgreSQL)   │  (not internet-exposed)
        │  aiogram + use cases     │   └─────────┬─────────┘
        └───────────┬──────────────┘             │
                    │                             ▼
             ┌──────▼───────┐              ┌──────────────┐
             │ volume:      │              │ volume:      │
             │ /data/backups│              │ pg data      │
             └──────┬───────┘              └──────────────┘
                    │ replicated off-box
                    ▼
             ┌──────────────────────┐
             │ off-site backup target│  (object storage / remote host)
             │  + encryption key kept │
             │  separately            │
             └──────────────────────┘
```

Containers (via `docker compose`):
- **bot** — the application (Telegram adapter + core). Runs migrations on deploy
  (or a dedicated one-shot migration step), then starts the bot.
- **db** — PostgreSQL, on a private Docker network only. Never publish `5432` to
  the internet.
- **reverse proxy** — terminates TLS; forwards only the webhook path to the bot
  (webhook mode). Not needed for polling mode.
- (optional) **backup/scheduler** — periodic backups (can also run in-process in
  the bot container via the scheduler adapter, authored by the system actor).

Volumes: `pg data`, `/data/backups`.

> **No receipts volume in v1.** Receipts (file attachments) are a **Version 2**
> feature; v1 stores no files, so there is no `/data/receipts` volume. See
> [`ROADMAP.md`](./ROADMAP.md).

---

## 2. Webhook vs polling

- **Webhook (recommended for production):** Telegram pushes updates to
  `WEBHOOK_BASE_URL` over HTTPS; requires a valid certificate and a public domain.
  Validate `WEBHOOK_SECRET` on every request.
- **Polling (simple/fallback):** the bot long-polls Telegram; no inbound ports or
  certificate needed. Fine for small scale or early stages.

Chosen via `BOT_MODE` (see [`CONFIGURATION.md`](./CONFIGURATION.md)).

---

## 3. Startup sequence

1. Load & validate configuration (fail fast on missing secrets).
2. Wait for the database to be ready.
3. **Run Alembic migrations** under the privileged `MIGRATION_DB_USER` (this role
   also installs the append-only triggers and grants the least-privilege app role
   per the privilege matrix).
4. **Seed on first run** (idempotent): roles, permissions, role–permission map,
   the reserved **system actor**, expense categories, default settings, and the
   **first Super Admin** from `FIRST_SUPER_ADMIN_TELEGRAM_ID`. See
   [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) §12.
5. Start the bot connecting as the least-privilege `APP_DB_USER`
   (no `UPDATE`/`DELETE` on strictly append-only tables — defense in depth for I2).
6. On start, run the **missed-backup catch-up** check (§5.2).
7. Register webhook (webhook mode) or begin polling.

> Migrations and the running app use **different DB roles** on purpose. See
> [`SECURITY.md`](./SECURITY.md) §4 and the privilege matrix in
> [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) §11.

---

## 4. Environments

| Environment | Purpose | Notes |
|-------------|---------|-------|
| Development | Local dev | polling mode, local Postgres, sample seed |
| Staging (optional) | Pre-prod validation | separate bot token + DB |
| Production | Live | webhook + TLS, backups on, monitoring |

Never share a bot token between environments; a token controls the live bot.

---

## 5. Backups

Backups satisfy the requirement for **scheduled automatic** and **manual**
backups, plus a controlled **restore** (§6).

### 5.1 What is backed up
- **PostgreSQL** logical dump (`pg_dump`) — the ledger, RBAC, audit, settings,
  donation-account history. This is the critical, irreplaceable data.
- (v1 stores no receipts/files, so there is nothing else to archive.)
- Config/secrets are **not** in backups; they are provisioned separately.

### 5.2 Scheduled automatic backups
- Driven by `BACKUP_SCHEDULE_CRON` (default daily 02:00 org time), authored by the
  **system actor**.
- Each run: `pg_dump` → compress → **encrypt** with `BACKUP_ENCRYPTION_KEY` →
  write to `BACKUP_DIR` with a timestamped name → **replicate off the VPS** to
  `BACKUP_OFFSITE_TARGET`.
- Retention: prune local backups older than `BACKUP_RETENTION_DAYS`.
- Success/failure is **audited**; failures notify Super Admins.
- **Missed-run catch-up:** if the bot was down at the scheduled time, a backup is
  taken on next start if the last successful backup is older than the interval, so
  a restart at the wrong minute does not silently skip a day.

### 5.3 Manual backups
- A Super Admin triggers "Run backup now" from the bot (`backup.manage`), or an
  operator runs the documented command on the host.
- Produces the same encrypted, off-box-replicated artifacts; audited.

### 5.4 Off-box key & copies (anti-tamper)
- The `BACKUP_ENCRYPTION_KEY` is stored **off the VPS**, separate from the backup
  archives, so a single host compromise cannot yield both the ciphertext and the
  key.
- Off-box replication also means an attacker who takes the VPS cannot destroy the
  only copy of history. See [`SECURITY.md`](./SECURITY.md) §4.2, §8.

### 5.5 Backup integrity
- Periodically **test-restore** into a throwaway environment to prove backups are
  usable (a backup never verified is not a backup).

---

## 6. Restore — operator-only host procedure (⚠️ exceptional)

Restore is **not** an in-bot action and there is **no** restore button or
permission. A restore can overwrite the entire immutable ledger and even wipe the
in-database audit log, so it is a deliberate, rare, disaster-recovery operation
performed on the host by a trusted operator. (See the admin/restore threat in
[`SECURITY.md`](./SECURITY.md) §4.2.)

**Procedure:**
1. Announce/record intent **off-box** first: who, when, why, which backup — in an
   external record (operator log / ticket), because the in-DB audit may be
   replaced by the restore (BR-AU5).
2. Put the bot in maintenance (stop the app container).
3. Retrieve the chosen backup and the encryption key (from their separate,
   off-box locations) and decrypt.
4. Restore into a **clean** database, then swap it in (do not restore over the
   live DB in place).
5. Run Alembic migrations to `head` (in case the backup predates schema changes).
6. Restart the bot; verify balance and recent reports against expectations.
7. Finalize the **off-box** restore record with the outcome.

**Controls & accountability:**
- Reserve restore for genuine disaster recovery (data loss/corruption), never as a
  way to "undo" legitimately recorded entries — that is what reversals are for.
- Governance resilience (≥2 Super Admins, [`USER_ROLES.md`](./USER_ROLES.md) §5)
  and off-box records make an improper restore **detectable and accountable**.

---

## 7. Observability & health

- **Health check** endpoint/command for the bot (liveness) and a DB connectivity
  check (readiness).
- **Structured logs** shipped to the host's logging; **no PII** and **no private
  free text** ever logged (see [`SECURITY.md`](./SECURITY.md) §9).
- Alert on: backup failure, DB connection loss, webhook errors, unhandled
  exceptions.
- Metrics (designed-for): entries recorded per period, report latency, error rate.

---

## 8. Upgrades / releases

- Immutable image tags; deploy by tag, not `latest`.
- Roll forward: build image → run migrations → deploy new image. Migrations are
  **additive and backward-compatible** wherever possible so a rollback of the app
  image does not break on the new schema.
- Keep a tested rollback plan (previous image + known-good backup).
- See [`ROADMAP.md`](./ROADMAP.md) for phased delivery.

---

## 9. Hardening checklist (production)

- [ ] Database not published to the internet; only the proxy is public.
- [ ] TLS with a valid certificate; `WEBHOOK_SECRET` validated.
- [ ] App runs as least-privilege DB role; migrations as separate role.
- [ ] Append-only triggers enabled on ledger/audit/settings-history/donation-accounts.
- [ ] `entry_annotations` trigger permits only redaction-shaped updates.
- [ ] Secrets from env/secret manager; none committed; bot token rotated if leaked.
- [ ] Encrypted backups, **off-box copy**, **encryption key stored separately**,
      tested restore.
- [ ] Restore is host-only and recorded off-box; ≥2 Super Admins configured.
- [ ] Firewall limits inbound to 80/443; SSH key-only.
- [ ] Logs contain no PII / no private free text; log retention set.
- [ ] Container runs as non-root; images pinned by digest/tag.
