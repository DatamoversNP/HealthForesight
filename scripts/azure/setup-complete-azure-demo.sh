#!/usr/bin/env bash
# =============================================================================
# Azure PostgreSQL demo: migrations, WIPE all existing app data, then seed fresh
# (users, 32 policies, pipelines, policy workspace, baseline, predicted impact,
# sample observations, canonical/source table row-count report).
#
# Wipe = TRUNCATE ALL public application tables (CASCADE) except alembic_version.
# That removes all product data (users, claims, policies, etc.). Schema and
# migration history stay. Use SKIP_WIPE=1 only if you intentionally keep rows.
#
# Usage (repo root) — substitute YOUR real Azure values:
#   export DATABASE_URL='postgresql+psycopg2://myadmin:Secret@myserver.postgres.database.azure.com:5432/mydb?sslmode=require'
#   ./scripts/azure/setup-complete-azure-demo.sh
#
# Optional environment:
#   SKIP_WIPE=1                Do not truncate tables (idempotent-ish re-seed only)
#   SKIP_MIGRATIONS=1          Skip alembic upgrade head
#   SKIP_USERS=1               Skip scripts/seed_users.py
#   SKIP_32_POLICIES=1         Skip apps/api/scripts/seed_all_32_policies.py
#   SKIP_PIPELINES=1           Skip apps/api/scripts/seed_all_comprehensive_pipelines.py
#   SKIP_POLICY_WORKSPACE=1    Skip apps/api/scripts/seed_complete_policy_workspace.py
#   SKIP_DEMO_NARRATIVE=1      Skip run_demo_day (baseline, predicted impact, observations)
#   SKIP_CANONICAL_CHECK=1     Skip scripts/check_canonical_source_data.py (claims/enrollment/etc.)
#   REGENERATE_PREDICTED_IMPACT=1  Replace predicted impact with full Stage 3.5 payload
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "❌ Set DATABASE_URL to your Azure PostgreSQL connection string."
  exit 1
fi
# Trailing space after ?sslmode=require breaks psycopg2 (invalid sslmode "require ")
export DATABASE_URL="$(printf '%s' "$DATABASE_URL" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "❌ DATABASE_URL is empty after trimming whitespace."
  exit 1
fi
if [[ "$DATABASE_URL" == *"YOURSERVER"* ]] || [[ "$DATABASE_URL" == *"YOURDB"* ]] || \
   [[ "$DATABASE_URL" == *"ADMIN:PASSWORD@"* ]] || [[ "$DATABASE_URL" == *"USER:PASS@"* ]] || \
   [[ "$DATABASE_URL" == *"@HOST.postgres"* ]] || [[ "$DATABASE_URL" == *"HOST.postgres.database.azure.com"* ]]; then
  echo "❌ DATABASE_URL still looks like a documentation placeholder."
  echo "   Use your real server name, user, password, and database from Azure Portal → Connection strings."
  exit 1
fi

export PYTHONPATH="${REPO_ROOT}/apps/api/src:${REPO_ROOT}/packages/common/src"
unset CORS_ORIGINS 2>/dev/null || true

echo "=========================================="
echo "Complete Azure demo data setup"
echo "=========================================="

if [[ -z "${SKIP_MIGRATIONS:-}" ]]; then
  echo ">>> [1/9] Alembic upgrade head..."
  cd "$REPO_ROOT/apps/api"
  python3 -m alembic upgrade head
  cd "$REPO_ROOT"
else
  echo ">>> [1/9] Skipping migrations (SKIP_MIGRATIONS=1)"
fi

if [[ -z "${SKIP_WIPE:-}" ]]; then
  echo ">>> [2/9] Wiping existing data (all public tables except alembic_version)..."
  SETUP_COMPLETE_AZURE_DEMO_WIPE=1 python3 scripts/wipe_public_application_data.py
else
  echo ">>> [2/9] Skipping wipe (SKIP_WIPE=1)"
fi

if [[ -z "${SKIP_USERS:-}" ]]; then
  echo ">>> [3/9] Seed users & roles (Swan@1234)..."
  python3 scripts/seed_users.py
else
  echo ">>> [3/9] Skipping users (SKIP_USERS=1)"
fi

if [[ -z "${SKIP_32_POLICIES:-}" ]]; then
  echo ">>> [4/9] Seed up to 32 policies..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_all_32_policies.py
  cd "$REPO_ROOT"
else
  echo ">>> [4/9] Skipping 32-policy seed (SKIP_32_POLICIES=1)"
fi

if [[ -z "${SKIP_PIPELINES:-}" ]]; then
  echo ">>> [5/9] Seed comprehensive pipelines..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_all_comprehensive_pipelines.py
  cd "$REPO_ROOT"
else
  echo ">>> [5/9] Skipping pipelines (SKIP_PIPELINES=1)"
fi

if [[ -z "${SKIP_DEMO_NARRATIVE:-}" ]]; then
  echo ">>> [6/9] Baseline + predicted impact for ALL policies (no observations yet)..."
  DEMO_PRED_CMD=(python3 scripts/run_demo_day.py --predicted-all --no-observations)
  if [[ -n "${REGENERATE_PREDICTED_IMPACT:-}" ]]; then
    DEMO_PRED_CMD+=(--regenerate-predicted-impact)
  fi
  "${DEMO_PRED_CMD[@]}"
else
  echo ">>> [6/9] Skipping demo baseline/predicted (SKIP_DEMO_NARRATIVE=1)"
fi

if [[ -z "${SKIP_POLICY_WORKSPACE:-}" ]]; then
  echo ">>> [7/9] Policy workspace (assumptions, versions, changelog, decisions, risks)..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_complete_policy_workspace.py
  cd "$REPO_ROOT"
else
  echo ">>> [7/9] Skipping policy workspace (SKIP_POLICY_WORKSPACE=1)"
fi

if [[ -z "${SKIP_DEMO_NARRATIVE:-}" ]]; then
  echo ">>> [8/9] Demo observations (5 policies, mixed verdicts)..."
  python3 scripts/run_demo_day.py --skip-seed
else
  echo ">>> [8/9] Skipping observations (SKIP_DEMO_NARRATIVE=1)"
fi

if [[ -z "${SKIP_CANONICAL_CHECK:-}" ]]; then
  echo ">>> [9/9] Canonical / source data check (claims_lines, enrollment_records, …)..."
  python3 "$REPO_ROOT/scripts/check_canonical_source_data.py"
else
  echo ">>> [9/9] Skipping canonical check (SKIP_CANONICAL_CHECK=1)"
fi

echo ""
echo "=========================================="
echo "✅ Complete demo setup finished"
echo "=========================================="
echo ""
echo "Login (seed_users): demo@example.com or admin@healthforesight.com / Swan@1234"
echo ""
echo "Note: Canonical claims/enrollment are NOT bulk-loaded here."
echo "      For Jan 2023–Dec 2025 synthetic history + DB baselines from claims, run:"
echo "      ./scripts/azure/setup-azure-fresh-historical-demo.sh (same DATABASE_URL)."
echo ""
