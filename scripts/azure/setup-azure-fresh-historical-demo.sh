#!/usr/bin/env bash
# =============================================================================
# Azure PostgreSQL: full demo WITH synthetic historical canonical data
# (Jan 2023 – Dec 2025 by default), tenant + optional per-policy baselines from
# claims, then predicted impact for all policies (same narrative as complete demo).
#
# DATA LOSS: By default this TRUNCATES every public application table (CASCADE),
# i.e. full product wipe — same as setup-complete-azure-demo.sh. Preserves only
# alembic_version. Set SKIP_WIPE=1 to keep existing rows (not recommended for
# a "fresh" demo).
#
# Usage (repo root) — substitute YOUR real Azure values (do not use USER/HOST/DBNAME literally):
#   export DATABASE_URL='postgresql+psycopg2://myadmin:Secret@myserver.postgres.database.azure.com:5432/mydb?sslmode=require'
#   ./scripts/azure/setup-azure-fresh-historical-demo.sh
#
# Inherits SKIP_* from setup-complete-azure-demo.sh where applicable, plus:
#   SKIP_SYNTHETIC_HISTORICAL=1   Skip synthetic load + baseline refresh (metadata-only demo)
#   SKIP_POLICY_BASELINES=1      Only tenant-level baseline from claims (faster)
#   SYNTH_MEMBERS=1200            Synthetic unique members (default ≥1000)
#   SYNTH_CLAIMS_MIN=120          Min claims per calendar month
#   SYNTH_CLAIMS_MAX=450          Max claims per calendar month
#   SYNTH_ALLOW_FEWER_MEMBERS=1 Pass --allow-fewer-members if SYNTH_MEMBERS < 1000
#   POLICY_CLAIMS_PER_MONTH=12   Supplemental claims per policy per month (scope alignment)
#   REGENERATE_PREDICTED_IMPACT=1  Re-run Stage 3.5 predicted impact (replace stub rows)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "❌ Set DATABASE_URL to your Azure PostgreSQL connection string."
  exit 1
fi
export DATABASE_URL="$(printf '%s' "$DATABASE_URL" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
if [[ "$DATABASE_URL" == *"YOURSERVER"* ]] || [[ "$DATABASE_URL" == *"YOURDB"* ]] || \
   [[ "$DATABASE_URL" == *"ADMIN:PASSWORD@"* ]] || [[ "$DATABASE_URL" == *"USER:PASS@"* ]] || \
   [[ "$DATABASE_URL" == *"@HOST.postgres"* ]] || [[ "$DATABASE_URL" == *"HOST.postgres.database.azure.com"* ]]; then
  echo "❌ DATABASE_URL still looks like a documentation placeholder."
  echo "   Use your real Azure PostgreSQL host (e.g. myserver.postgres.database.azure.com), user, password, and database."
  echo "   Azure Portal → your server → Connection strings (or Overview for the server FQDN)."
  exit 1
fi

export PYTHONPATH="${REPO_ROOT}/apps/api/src:${REPO_ROOT}/packages/common/src"
unset CORS_ORIGINS 2>/dev/null || true

SYNTH_MEMBERS="${SYNTH_MEMBERS:-1200}"
SYNTH_CLAIMS_MIN="${SYNTH_CLAIMS_MIN:-120}"
SYNTH_CLAIMS_MAX="${SYNTH_CLAIMS_MAX:-450}"
HIST_START="${HIST_START:-2023-01-01}"
HIST_END="${HIST_END:-2025-12-31}"

POLICY_BASELINE_ARGS=()
if [[ -z "${SKIP_POLICY_BASELINES:-}" ]]; then
  POLICY_BASELINE_ARGS=(--policy-baselines)
fi

echo "=========================================="
echo "Azure fresh demo + synthetic historical data"
echo "=========================================="
if [[ -z "${SKIP_WIPE:-}" ]]; then
  echo "⚠️  Full wipe: all public app tables will be TRUNCATED (set SKIP_WIPE=1 to keep data)."
else
  echo "SKIP_WIPE=1 — existing public data will NOT be truncated."
fi

if [[ -z "${SKIP_MIGRATIONS:-}" ]]; then
  echo ">>> [1/11] Alembic upgrade head..."
  cd "$REPO_ROOT/apps/api"
  python3 -m alembic upgrade head
  cd "$REPO_ROOT"
else
  echo ">>> [1/11] Skipping migrations (SKIP_MIGRATIONS=1)"
fi

if [[ -z "${SKIP_WIPE:-}" ]]; then
  echo ">>> [2/11] Wiping existing data..."
  SETUP_COMPLETE_AZURE_DEMO_WIPE=1 python3 scripts/wipe_public_application_data.py
else
  echo ">>> [2/11] Skipping wipe (SKIP_WIPE=1)"
fi

if [[ -z "${SKIP_USERS:-}" ]]; then
  echo ">>> [3/11] Seed users & roles..."
  python3 scripts/seed_users.py
else
  echo ">>> [3/11] Skipping users (SKIP_USERS=1)"
fi

if [[ -z "${SKIP_32_POLICIES:-}" ]]; then
  echo ">>> [4/11] Seed up to 32 policies..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_all_32_policies.py
  cd "$REPO_ROOT"
else
  echo ">>> [4/11] Skipping 32-policy seed (SKIP_32_POLICIES=1)"
fi

if [[ -z "${SKIP_PIPELINES:-}" ]]; then
  echo ">>> [5/11] Seed comprehensive pipelines..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_all_comprehensive_pipelines.py
  cd "$REPO_ROOT"
else
  echo ">>> [5/11] Skipping pipelines (SKIP_PIPELINES=1)"
fi

if [[ -z "${SKIP_SYNTHETIC_HISTORICAL:-}" ]]; then
  echo ">>> [6/11] Synthetic historical → Postgres (claims, enrollment, providers)..."
  # Build argv in one array — with set -u, "${empty[@]}" is an error; never expand an empty optional array.
  POLICY_CLAIMS_PER_MONTH="${POLICY_CLAIMS_PER_MONTH:-12}"
  LOAD_CMD=(
    python3 scripts/load_synthetic_historical_to_postgres.py
    --start "$HIST_START"
    --end "$HIST_END"
    --members "$SYNTH_MEMBERS"
    --claims-min-per-month "$SYNTH_CLAIMS_MIN"
    --claims-max-per-month "$SYNTH_CLAIMS_MAX"
    --policy-claims-per-month "$POLICY_CLAIMS_PER_MONTH"
  )
  if [[ -n "${SYNTH_ALLOW_FEWER_MEMBERS:-}" ]]; then
    LOAD_CMD+=(--allow-fewer-members)
  fi
  "${LOAD_CMD[@]}"

  echo ">>> [7/11] Baselines from canonical claims (--replace)..."
  REFRESH_CMD=(python3 scripts/refresh_baseline_from_canonical.py --replace --start "$HIST_START" --end "$HIST_END")
  if [[ ${#POLICY_BASELINE_ARGS[@]} -gt 0 ]]; then
    REFRESH_CMD+=("${POLICY_BASELINE_ARGS[@]}")
  fi
  "${REFRESH_CMD[@]}"
else
  echo ">>> [6–7/11] Skipping synthetic load + baseline refresh (SKIP_SYNTHETIC_HISTORICAL=1)"
fi

if [[ -z "${SKIP_DEMO_NARRATIVE:-}" ]]; then
  echo ">>> [8/11] Predicted impact for ALL policies (no observations yet)..."
  DEMO_PRED_CMD=(python3 scripts/run_demo_day.py --predicted-all --no-observations)
  if [[ -n "${REGENERATE_PREDICTED_IMPACT:-}" ]]; then
    DEMO_PRED_CMD+=(--regenerate-predicted-impact)
  fi
  "${DEMO_PRED_CMD[@]}"
else
  echo ">>> [8/11] Skipping demo narrative (SKIP_DEMO_NARRATIVE=1)"
fi

if [[ -z "${SKIP_POLICY_WORKSPACE:-}" ]]; then
  echo ">>> [9/11] Policy workspace seed..."
  cd "$REPO_ROOT/apps/api"
  python3 scripts/seed_complete_policy_workspace.py
  cd "$REPO_ROOT"
else
  echo ">>> [9/11] Skipping policy workspace (SKIP_POLICY_WORKSPACE=1)"
fi

if [[ -z "${SKIP_DEMO_NARRATIVE:-}" ]]; then
  echo ">>> [10/11] Demo observations..."
  python3 scripts/run_demo_day.py --skip-seed
else
  echo ">>> [10/11] Skipping observations (SKIP_DEMO_NARRATIVE=1)"
fi

if [[ -z "${SKIP_CANONICAL_CHECK:-}" ]]; then
  echo ">>> [11/11] Canonical / source data check..."
  python3 "$REPO_ROOT/scripts/check_canonical_source_data.py"
else
  echo ">>> [11/11] Skipping canonical check (SKIP_CANONICAL_CHECK=1)"
fi

echo ""
echo "=========================================="
echo "✅ Fresh historical demo setup finished"
echo "=========================================="
echo ""
echo "Login: demo@example.com or admin@healthforesight.com / Swan@1234"
echo "Historical window: $HIST_START .. $HIST_END (override with HIST_START / HIST_END)"
echo ""
