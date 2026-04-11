#!/usr/bin/env bash
# =============================================================================
# Run DB migrations + seed users (admin@healthforesight.com / Swan@1234) on Azure Postgres.
# For full demo (32 policies, pipelines, workspace, baselines, observations), use:
#   ./scripts/azure/setup-complete-azure-demo.sh
#
# You need the SAME connection string as on healthforesight-api (Configuration → DATABASE_URL).
#
# Usage (from repo root):
#   export DATABASE_URL='postgresql://USER:PASS@HOST.postgres.database.azure.com:5432/DB?sslmode=require'
#   ./scripts/azure/seed-azure-db.sh
#
# Or one line:
#   DATABASE_URL='postgresql://...' ./scripts/azure/seed-azure-db.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${DATABASE_URL:-}" ]] || [[ "$DATABASE_URL" == *"@host:"* ]]; then
  echo "❌ Set DATABASE_URL to your real Azure PostgreSQL connection string (not the doc placeholder)."
  exit 1
fi
export DATABASE_URL="$(printf '%s' "$DATABASE_URL" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
# Reject copy-paste placeholders from docs
if [[ "$DATABASE_URL" == *"YOURSERVER"* ]] || [[ "$DATABASE_URL" == *"YOURDB"* ]] || \
   [[ "$DATABASE_URL" == *":ADMIN:"* ]] || [[ "$DATABASE_URL" == *"ADMIN:PASSWORD@"* ]]; then
  echo "❌ DATABASE_URL still contains placeholders (YOURSERVER, YOURDB, ADMIN, PASSWORD)."
  echo ""
  echo "Use your REAL values from Azure Portal:"
  echo "  1. PostgreSQL server → Overview → copy 'Server name' (e.g. mydb-xyz.postgres.database.azure.com)"
  echo "  2. Server admin login name (e.g. myadmin) + the password you set when creating the server"
  echo "  3. Database name (create one under Databases if needed, e.g. uepi)"
  echo ""
  echo "Format:"
  echo "  export DATABASE_URL='postgresql://ADMIN_USER:YOUR_REAL_PASSWORD@SERVER_NAME.postgres.database.azure.com:5432/DATABASE_NAME?sslmode=require'"
  echo ""
  echo "Special characters in password: URL-encode them (e.g. @ → %40, # → %23) or use Azure 'Connection strings' from the DB blade."
  exit 1
fi

export PYTHONPATH="${REPO_ROOT}/apps/api/src:${REPO_ROOT}/packages/common/src"
unset CORS_ORIGINS 2>/dev/null || true

echo ">>> Alembic upgrade (apps/api)..."
cd "$REPO_ROOT/apps/api"
python3 -m alembic upgrade head

cd "$REPO_ROOT"
echo ">>> Seed users (password Swan@1234 for all seeded emails)..."
python3 scripts/seed_users.py

echo ""
echo "✅ Done. Try login: admin@healthforesight.com / Swan@1234"
