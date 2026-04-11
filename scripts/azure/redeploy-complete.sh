#!/usr/bin/env bash
# =============================================================================
# HealthForesight — complete Azure redeploy (one script)
# =============================================================================
# Runs, in order:
#   1. Optional: fix API CORS for the web origins (gateway + CORS_ORIGINS app setting)
#   2. Optional: Alembic upgrade head against DATABASE_URL (local CLI → Azure Postgres)
#   3. API: Docker build in ACR + configure App Service + restart (deploy-api-docker.sh)
#   4. Web: Build SPA + Node proxy + zip deploy (deploy-web-appservice-full.sh)
#   5. HTTP verification: /api/v1/ping on API and web (unless SKIP_VERIFY=1)
#
# From repository root:
#   ./scripts/azure/redeploy-complete.sh
#   ./scripts/azure/redeploy-complete.sh --api-only
#   ./scripts/azure/redeploy-complete.sh --web-only
#
# Environment overrides (optional):
#   RESOURCE_GROUP   default: healthforesight-rg
#   API_APP_NAME     default: healthforesight-api
#   WEB_APP_NAME     default: healthforesight-web
#   ACR_NAME         default: healthforesightacr
#   API_BACKEND      default: https://${API_APP_NAME}.azurewebsites.net
#   FRONTEND_ORIGIN  default: https://${WEB_APP_NAME}.azurewebsites.net  (for CORS script)
#   DATABASE_URL     if set and SKIP_MIGRATIONS unset → alembic upgrade head before deploy
#   SKIP_CORS=1      skip ./fix-cors-for-frontend.sh
#   SKIP_MIGRATIONS=1 skip database migrations
#   SKIP_VERIFY=1    skip post-deploy curl checks (forwarded to redeploy-all.sh)
#   VITE_AUTH_STORAGE optional: session → passed through redeploy-all → web deploy
#
# Prerequisites:
#   az login, Node.js + npm, zip, Python 3 + alembic (only if running migrations)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export WEB_APP_NAME="${WEB_APP_NAME:-healthforesight-web}"
export ACR_NAME="${ACR_NAME:-healthforesightacr}"
export API_BACKEND="${API_BACKEND:-https://${API_APP_NAME}.azurewebsites.net}"
export FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-https://${WEB_APP_NAME}.azurewebsites.net}"

echo "=============================================="
echo "HealthForesight — COMPLETE REDEPLOY"
echo "=============================================="
echo "REPO_ROOT:        $REPO_ROOT"
echo "Resource group:   $RESOURCE_GROUP"
echo "API app:          $API_APP_NAME"
echo "Web app:          $WEB_APP_NAME"
echo "ACR:              $ACR_NAME"
echo "API backend URL:  $API_BACKEND"
echo "Frontend origin:  $FRONTEND_ORIGIN (CORS)"
echo "Skip CORS:        ${SKIP_CORS:-0}"
echo "Skip migrations:  ${SKIP_MIGRATIONS:-0}"
echo "Skip verify:      ${SKIP_VERIFY:-0}"
echo "=============================================="

if ! command -v az &>/dev/null; then
  echo "❌ Azure CLI (az) not found. https://aka.ms/InstallAzureCLI"
  exit 1
fi
if ! az account show &>/dev/null; then
  echo "❌ Not logged in. Run: az login"
  exit 1
fi

# --- 1) CORS (direct browser → API, or misconfigured proxy) ---
if [[ "${SKIP_CORS:-0}" != "1" ]]; then
  echo ""
  echo ">>> [CORS] API allowed origins + CORS_ORIGINS app setting ..."
  FRONTEND_ORIGIN="$FRONTEND_ORIGIN" \
    API_APP_NAME="$API_APP_NAME" \
    RESOURCE_GROUP="$RESOURCE_GROUP" \
    bash "$SCRIPT_DIR/fix-cors-for-frontend.sh" || {
    echo "⚠️  CORS script failed (continuing). Fix manually if the browser shows CORS errors."
  }
else
  echo ""
  echo ">>> [CORS] skipped (SKIP_CORS=1)"
fi

# --- 2) Database migrations (optional) ---
if [[ -z "${SKIP_MIGRATIONS:-}" ]] && [[ -n "${DATABASE_URL:-}" ]]; then
  echo ""
  echo ">>> [DB] Alembic upgrade head (DATABASE_URL is set) ..."
  export PYTHONPATH="${REPO_ROOT}/apps/api/src:${REPO_ROOT}/packages/common/src"
  (cd "${REPO_ROOT}/apps/api" && python3 -m alembic upgrade head) && echo "✅ Migrations OK" || {
    echo "❌ Migrations failed. Fix DATABASE_URL / network, then run:"
    echo "   cd apps/api && PYTHONPATH=src:../../packages/common/src python3 -m alembic upgrade head"
    exit 1
  }
elif [[ -z "${DATABASE_URL:-}" ]]; then
  echo ""
  echo ">>> [DB] Migrations skipped (DATABASE_URL not set). To run:"
  echo "    export DATABASE_URL='postgresql+psycopg2://...'"
  echo "    ./scripts/azure/redeploy-complete.sh"
else
  echo ""
  echo ">>> [DB] Migrations skipped (SKIP_MIGRATIONS set)"
fi

# --- 3–5) API + Web + verify (same as redeploy-all.sh) ---
echo ""
echo ">>> [Deploy] API (container) + Web (zip) + verification ..."
bash "$SCRIPT_DIR/redeploy-all.sh" "$@"

exit $?
