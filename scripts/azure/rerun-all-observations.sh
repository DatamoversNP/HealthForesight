#!/usr/bin/env bash
# Delete all observations for a tenant and regenerate ONE observation per policy
# (rolling ~365 days ending today). NOT weekly Q1 2026 — for that use:
#   ./scripts/azure/seed-q1-2026-weekly-observations.sh
#
# Run against Azure Postgres from your laptop:
#   export DATABASE_URL='postgresql://USER:PASS@HOST:5432/DB?sslmode=require'
#   ./scripts/azure/rerun-all-observations.sh
#   ./scripts/azure/rerun-all-observations.sh --tenant-id '00000000-0000-0000-0000-000000000001'
#
# If DATABASE_URL is unset, sources apps/api/.env when that file exists.
#
# Prerequisites: Python 3 + apps/api deps (pip install -r apps/api/requirements.txt).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY="$REPO_ROOT/scripts/delete_all_observations_and_regenerate_all.py"

if [[ ! -f "$PY" ]]; then
  echo "ERROR: missing $PY"
  exit 2
fi

if [[ -z "${DATABASE_URL:-}" && -f "$REPO_ROOT/apps/api/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO_ROOT/apps/api/.env" 2>/dev/null || true
  set +a
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: Set DATABASE_URL (Azure PostgreSQL), or define it in apps/api/.env"
  exit 2
fi

exec python3 "$PY" "$@"
