#!/usr/bin/env bash
# Container entrypoint. Placeholder wiring; real migration + run steps are added
# in later milestones (see docs/DEPLOYMENT.md §3 startup sequence).
set -euo pipefail

cmd="${1:-run}"

case "$cmd" in
  migrate)
    echo "[entrypoint] running database migrations (alembic upgrade head)"
    alembic upgrade head
    ;;
  run)
    echo "[entrypoint] starting donation-bot"
    exec python -m donation_bot
    ;;
  *)
    echo "[entrypoint] unknown command: $cmd (expected 'migrate' or 'run')" >&2
    exit 64
    ;;
esac
