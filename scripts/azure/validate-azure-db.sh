#!/usr/bin/env bash
# Validate baselines + policy predictive impact against the database the API uses.
# Intended for Azure PostgreSQL after deploy (or any Postgres with the same schema).
#
# Usage (from repo root):
#   export DATABASE_URL='postgresql://user:pass@host:5432/db?sslmode=require'
#   ./scripts/azure/validate-azure-db.sh [--tenant UUID] [--json]
#
# Or pass URL once (avoid shell history: use a file + --env-file on the Python side):
#   ./scripts/azure/validate-azure-db.sh --database-url 'postgresql://...' --tenant 00000000-0000-0000-0000-000000000001
#
# If DATABASE_URL is unset, loads apps/api/.env when present.
#
# Prerequisites: Python 3, apps/api dependencies (pip install -r apps/api/requirements.txt).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY="$REPO_ROOT/apps/api/scripts/validate_baselines_predictions_report.py"

if [[ ! -f "$PY" ]]; then
  echo "ERROR: missing $PY"
  exit 2
fi

if [[ -z "${DATABASE_URL:-}" && -f "$REPO_ROOT/apps/api/.env" ]]; then
  # shellcheck disable=SC1090
  set -a
  # shellcheck source=/dev/null
  source "$REPO_ROOT/apps/api/.env" 2>/dev/null || true
  set +a
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: Set DATABASE_URL to your Azure PostgreSQL connection string, or define it in apps/api/.env"
  echo "Example:"
  echo "  export DATABASE_URL='postgresql://USER:PASS@HOST:5432/DB?sslmode=require'"
  echo "  $0 --tenant 00000000-0000-0000-0000-000000000001"
  exit 2
fi

exec python3 "$PY" "$@"
