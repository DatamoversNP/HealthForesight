#!/usr/bin/env bash
# =============================================================================
# HealthForesight — final config + optional seed
# Uses values from this project. DATABASE_URL: from API app or env.
#
# Run from repo root:  ./scripts/azure/run-final-config.sh
#
# If API has DATABASE_URL set: seed runs automatically.
# If not: set it first in Portal, or: DATABASE_URL='postgresql://...' ./scripts/...
# =============================================================================
set -euo pipefail

RG="healthforesight-rg"
API="healthforesight-api"
WEB="healthforesight-web"
API_URL="https://healthforesight-api.azurewebsites.net"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=============================================="
echo "HealthForesight — final config"
echo "=============================================="
echo "RG:   $RG"
echo "API:  $API"
echo "WEB:  $WEB"
echo ""

# --- 1. API: clear startup + WEBSITES_PORT=8080 (matches docker-entrypoint.sh) ---
echo ">>> API: clear startup command..."
az webapp config set -g "$RG" -n "$API" --startup-command "" --output none 2>/dev/null || true
echo ">>> API: WEBSITES_PORT=8080..."
az webapp config appsettings set -g "$RG" -n "$API" --settings WEBSITES_PORT=8080 --output none 2>/dev/null || true

# --- 2. API: set DATABASE_URL if provided ---
if [[ -n "${DATABASE_URL:-}" ]] && [[ "$DATABASE_URL" != *"YOURSERVER"* ]] && [[ "$DATABASE_URL" != *"YOURDB"* ]]; then
  echo ">>> API: set DATABASE_URL..."
  az webapp config appsettings set -g "$RG" -n "$API" --settings "DATABASE_URL=$DATABASE_URL" --output none
else
  echo ">>> API: DATABASE_URL not in env (skip). Ensure it's set in Portal → $API → Configuration → Application settings."
fi

# --- 3. API restart ---
echo ">>> API: restart..."
az webapp restart -g "$RG" -n "$API" --output none

# --- 4. Web: proxy + Node ---
echo ">>> Web: API_BACKEND_URL + Node 20 + startup..."
az webapp config appsettings set -g "$RG" -n "$WEB" --settings \
  "API_BACKEND_URL=$API_URL" \
  "WEBSITE_NODE_DEFAULT_VERSION=~20" \
  --output none
az webapp config set -g "$RG" -n "$WEB" --linux-fx-version "NODE|20-lts" --output none
az webapp config set -g "$RG" -n "$WEB" --startup-command "node server.mjs" --output none 2>/dev/null || true

echo ">>> Web: restart..."
az webapp restart -g "$RG" -n "$WEB" --output none

# --- 5. Seed (if we can get DATABASE_URL from API) ---
echo ""
DB_URL=$(az webapp config appsettings list -g "$RG" -n "$API" --query "[?name=='DATABASE_URL'].value" -o tsv 2>/dev/null | head -1)
if [[ -n "$DB_URL" ]] && [[ "$DB_URL" != *"YOURSERVER"* ]] && [[ "$DB_URL" != *"YOURDB"* ]]; then
  echo ">>> Seed users (from API's DATABASE_URL)..."
  export DATABASE_URL="$DB_URL"
  export PYTHONPATH="${REPO_ROOT}/apps/api/src:${REPO_ROOT}/packages/common/src"
  unset CORS_ORIGINS 2>/dev/null || true
  cd "$REPO_ROOT/apps/api"
  if python3 -m alembic upgrade head 2>/dev/null; then
    cd "$REPO_ROOT"
    if python3 scripts/seed_users.py 2>/dev/null; then
      echo ">>> Seed OK."
    else
      echo ">>> Seed failed (check Postgres firewall / network)."
    fi
  else
    echo ">>> Migrations failed (DB unreachable from this machine?)."
  fi
  cd "$REPO_ROOT"
else
  echo ">>> Seed skipped: DATABASE_URL not set on API or unreachable. Set it in Portal and run:"
  echo "    ./scripts/azure/seed-azure-db.sh"
fi

echo ""
echo "=============================================="
echo "Done"
echo "=============================================="
echo "Web:  https://$WEB.azurewebsites.net"
echo "API:  https://$API.azurewebsites.net"
echo ""
echo "Login: admin@healthforesight.com / Swan@1234"
echo "=============================================="
