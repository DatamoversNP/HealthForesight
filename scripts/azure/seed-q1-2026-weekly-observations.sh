#!/usr/bin/env bash
# Q1 2026 (1 Jan – 31 Mar): load policy-scoped demo claims (Q1_2026_DEMO) and create
# one PERIODIC observation per ISO week per policy (~13 weeks × N policies).
#
# From repo root:
#   export DATABASE_URL='postgresql://...?sslmode=require'
#   ./scripts/azure/seed-q1-2026-weekly-observations.sh
#
# If you previously ran rerun-all-observations.sh (32 single observations), use --purge
# and --clear-all-observations-first (passed through to the Python seed):
#   ./scripts/azure/seed-q1-2026-weekly-observations.sh --purge --clear-all-observations-first
#
# Observations-only (Q1 demo claims already in DB):
#   ./scripts/azure/seed-q1-2026-weekly-observations.sh --observations-only
#
# If DATABASE_URL is unset, sources apps/api/.env when present.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY="$REPO_ROOT/scripts/seed_q1_2026_observations_demo.py"

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
  echo "ERROR: Set DATABASE_URL or apps/api/.env"
  exit 2
fi

exec python3 "$PY" "$@"
