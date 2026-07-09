# Configuration

> **Last updated:** 2026-07-09 (rev. after Phase 2.5 architecture review)
> Two kinds of configuration exist: **deploy-time** (environment variables, set by
> operators) and **runtime settings** (changed by Super Admins via the bot, stored
> in the `settings` table). This document is the single reference for both.

---

## 1. Principles

- **One typed config object.** Environment variables are loaded once, validated,
  and exposed as a typed settings object. Nothing else in the code reads
  `os.environ` directly.
- **Fail fast.** Missing/invalid required variables cause the app to refuse to
  start with a clear error — never silent defaults for secrets.
- **Secrets never in git.** `.env` is git-ignored; `.env.example` documents every
  key with a safe placeholder. See [`SECURITY.md`](./SECURITY.md) §7.
- **Deploy-time vs runtime split.** Anything an operator must set to boot goes in
  env; anything a Super Admin should change while running goes in `settings`.

---

## 2. Deploy-time environment variables

### Application
| Variable | Required | Example | Notes |
|----------|:--------:|---------|-------|
| `APP_ENV` | yes | `production` | `development` \| `production` |
| `LOG_LEVEL` | no | `INFO` | |
| `DEFAULT_LOCALE` | no | `uz` | v1 supports `uz`; `ru`/`en` designed-for |
| `ORG_TIMEZONE` | no | `Asia/Tashkent` | seeds the runtime `org.timezone` setting on first boot |

### Telegram
| Variable | Required | Example | Notes |
|----------|:--------:|---------|-------|
| `BOT_TOKEN` | **yes** | `123456:ABC...` | highly sensitive; keep out of logs |
| `BOT_MODE` | no | `webhook` | `webhook` \| `polling` |
| `WEBHOOK_BASE_URL` | if webhook | `https://bot.example.uz` | public HTTPS base |
| `WEBHOOK_SECRET` | if webhook | random string | validates incoming updates |
| `WEBHOOK_PORT` | no | `8080` | internal port behind reverse proxy |

### Database (PostgreSQL)
| Variable | Required | Example | Notes |
|----------|:--------:|---------|-------|
| `POSTGRES_HOST` | yes | `db` | private network name |
| `POSTGRES_PORT` | no | `5432` | |
| `POSTGRES_DB` | yes | `donation_bot` | |
| `APP_DB_USER` | yes | `donation_app` | least-privilege role (no UPDATE/DELETE on strictly append-only tables) |
| `APP_DB_PASSWORD` | **yes** | — | secret |
| `MIGRATION_DB_USER` | yes | `donation_migrator` | privileged role for Alembic/DDL |
| `MIGRATION_DB_PASSWORD` | **yes** | — | secret |

> Two DB roles enforce append-only defense in depth (see the privilege matrix in
> [`DATABASE_DESIGN.md`](./DATABASE_DESIGN.md) §11): the app role cannot
> `UPDATE`/`DELETE` strictly append-only tables (ledger, audit, settings history,
> donation accounts); migrations run under the privileged role.

### Bootstrap
| Variable | Required | Example | Notes |
|----------|:--------:|---------|-------|
| `FIRST_SUPER_ADMIN_TELEGRAM_ID` | **yes** | `987654321` | seeded as the first Super Admin on first run; also the idempotent **break-glass recovery** path (see [`USER_ROLES.md`](./USER_ROLES.md)) |
| `FIRST_SUPER_ADMIN_NAME` | no | `Bosh admin` | display name for audit readability |

### Backups
| Variable | Required | Example | Notes |
|----------|:--------:|---------|-------|
| `BACKUP_DIR` | no | `/data/backups` | where dumps are written before off-box copy |
| `BACKUP_SCHEDULE_CRON` | no | `0 2 * * *` | daily 02:00 org time |
| `BACKUP_RETENTION_DAYS` | no | `30` | prune older backups |
| `BACKUP_ENCRYPTION_KEY` | **yes if backups on** | — | encrypt dumps at rest; **store OFF the VPS**, separate from the backups themselves |
| `BACKUP_OFFSITE_TARGET` | recommended | `s3://…` / remote path | off-box replication destination (see [`DEPLOYMENT.md`](./DEPLOYMENT.md)) |

> **Not present in v1:** there is **no** restore-related environment variable and
> no in-bot restore. Restore is an operator-only host procedure
> ([`DEPLOYMENT.md`](./DEPLOYMENT.md)).

### Receipts / file storage — **Version 2 only**
Receipts are **not** part of v1, so **no storage environment variables are used in
v1** (`STORAGE_*`, `S3_*`, `MAX_RECEIPT_MB`). They will be introduced with the V2
receipts feature. See [`ROADMAP.md`](./ROADMAP.md).

### Future providers *(post-v1, not used in v1)*
| Variable | Required | Notes |
|----------|:--------:|-------|
| `CLICK_*`, `PAYME_*`, `UZCARD_*`, `HUMO_*`, `BANK_*` | no | provider keys/secrets; see [`API_INTEGRATIONS.md`](./API_INTEGRATIONS.md) |

---

## 3. Runtime settings (Super Admin, stored in `settings`)

Changed via the bot; every change is written to `settings_history` and audited.

| Setting key | Type | Default | Meaning |
|-------------|------|---------|---------|
| `org.name` | string | — | Organization display name |
| `org.timezone` | string | `Asia/Tashkent` | Report bucketing zone (BR-R4); changing it re-buckets historical days (BR-R5) and is audited |
| `expenses.block_overspend` | bool | `false` | Block vs warn when balance would go negative (best-effort under concurrency) (BR-E4) |
| `limits.amount_warn_threshold` | int (tiyin) | `100000000` (1,000,000 so'm) | Amounts at/above require an extra confirmation (BR-M4) |
| `limits.amount_max` | int (tiyin) | `10000000000` (100,000,000 so'm) | Amounts above are rejected (BR-M4) |
| `limits.backdate_window_days` | int | `30` | Max days an entry may be back-dated; beyond → rejected; within → confirmed (BR-L7) |
| `reports.public_channel_id` | string? | null | Optional channel for scheduled public reports (designed-for) |
| `reports.auto_post_schedule` | string? | null | Cron for scheduled report posting (designed-for) |

> The default amount thresholds above are illustrative and tuned to the
> organization during setup. Rule of thumb: if changing it should **not** require a
> redeploy and is a business/policy choice, it belongs here — not in env.

---

## 4. `.env.example` (illustrative)

```dotenv
# --- Application ---
APP_ENV=production
LOG_LEVEL=INFO
DEFAULT_LOCALE=uz
ORG_TIMEZONE=Asia/Tashkent

# --- Telegram ---
BOT_TOKEN=CHANGE_ME
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.example.uz
WEBHOOK_SECRET=CHANGE_ME_RANDOM

# --- Database ---
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=donation_bot
APP_DB_USER=donation_app
APP_DB_PASSWORD=CHANGE_ME
MIGRATION_DB_USER=donation_migrator
MIGRATION_DB_PASSWORD=CHANGE_ME

# --- Bootstrap ---
FIRST_SUPER_ADMIN_TELEGRAM_ID=000000000
FIRST_SUPER_ADMIN_NAME=Bosh admin

# --- Backups ---
BACKUP_DIR=/data/backups
BACKUP_SCHEDULE_CRON=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_ENCRYPTION_KEY=CHANGE_ME          # store OFF the VPS, separate from backups
BACKUP_OFFSITE_TARGET=CHANGE_ME          # e.g. s3://bucket/path or remote host

# Receipts / STORAGE_* / S3_* : Version 2 only — not used in v1
# Provider keys (CLICK_*, PAYME_*, ...) : post-v1 — not used in v1
```

> This is a documentation illustration. The authoritative `.env.example` file is
> created in Phase 3 alongside the implementation.
