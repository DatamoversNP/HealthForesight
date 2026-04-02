#!/usr/bin/env bash
# =============================================================================
# HealthForesight – Complete deployment (same links as before)
# =============================================================================
# Deploys API + Frontend, configures CORS, runs DB migrations, seeds users.
# Uses: healthforesight-rg, healthforesight-api, healthforesight-web
#
# Prerequisites:
#   - Azure CLI logged in (az login)
#   - DATABASE_URL set to your Azure PostgreSQL connection string (for migrations + seed)
#   - Optional: JWT_SECRET set in Azure Web App (or use default for dev)
#
# Usage (from repo root):
#   export DATABASE_URL="postgresql://user:pass@server.postgres.database.azure.com:5432/dbname?sslmode=require"
#   ./scripts/azure/deploy-complete-full.sh
#
# Skip DB steps (deploy only):
#   SKIP_MIGRATIONS=1 SKIP_SEED=1 ./scripts/azure/deploy-complete-full.sh
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Same app names as before
export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
export API_URL="https://$API_APP_NAME.azurewebsites.net"
FRONTEND_SWA_URL="https://$STATIC_WEB_APP_NAME.azurestaticapps.net"
FRONTEND_WEBAPP_URL="https://$STATIC_WEB_APP_NAME.azurewebsites.net"

echo "=============================================="
echo "HealthForesight – Complete deployment"
echo "=============================================="
echo ""
echo "Resource group:  $RESOURCE_GROUP"
echo "API:             $API_APP_NAME  →  $API_URL"
echo "Frontend:        $STATIC_WEB_APP_NAME  →  $FRONTEND_SWA_URL (or .azurewebsites.net)"
echo ""

# -----------------------------------------------------------------------------
# Step 0: Configure API app settings (CORS so frontend can call API)
# -----------------------------------------------------------------------------
echo "--- Step 0: Configure API (CORS for frontend) ---"
CORS_ORIGINS="$FRONTEND_SWA_URL,$FRONTEND_WEBAPP_URL,http://localhost:3050,http://localhost:3000"
if az webapp show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none 2>/dev/null; then
  az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --settings "CORS_ORIGINS=$CORS_ORIGINS" \
    --output none 2>/dev/null || true
  echo "CORS_ORIGINS set for API."
else
  echo "API app not found; Step 0 skipped. Create the Web App first or check names."
fi
echo ""

# -----------------------------------------------------------------------------
# Step 1: Deploy API
# -----------------------------------------------------------------------------
echo "--- Step 1: Deploy API ---"
"$SCRIPT_DIR/deploy-api.sh"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Deploy Frontend (build points to same API URL)
# -----------------------------------------------------------------------------
echo "--- Step 2: Deploy Frontend ---"
export API_URL="$API_URL"
"$SCRIPT_DIR/deploy-frontend.sh"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Database migrations (if DATABASE_URL set and not skipped)
# -----------------------------------------------------------------------------
if [ -z "${SKIP_MIGRATIONS}" ] && [ -n "${DATABASE_URL}" ]; then
  echo "--- Step 3: Run database migrations ---"
  cd "$PROJECT_ROOT/apps/api" || exit 1
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  if python3 -m alembic upgrade head 2>/dev/null; then
    echo "Migrations completed."
  else
    echo "Warning: migrations failed. Check DATABASE_URL and network. Run manually:"
    echo "  cd apps/api && PYTHONPATH=../src:../../packages/common/src alembic upgrade head"
  fi
  cd "$PROJECT_ROOT" || exit 1
  echo ""
elif [ -z "${DATABASE_URL}" ]; then
  echo "--- Step 3: Migrations skipped (DATABASE_URL not set) ---"
  echo "Set DATABASE_URL and run: cd apps/api && alembic upgrade head"
  echo ""
fi

# -----------------------------------------------------------------------------
# Step 4: Seed users (password Swan@1234)
# -----------------------------------------------------------------------------
if [ -z "${SKIP_SEED}" ] && [ -n "${DATABASE_URL}" ]; then
  echo "--- Step 4: Seed users ---"
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  if python3 "$PROJECT_ROOT/scripts/seed_users.py" 2>/dev/null; then
    echo "User seed completed."
  else
    echo "Warning: user seed failed. Run manually:"
    echo "  PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py"
  fi
  echo ""
elif [ -z "${DATABASE_URL}" ]; then
  echo "--- Step 4: User seed skipped (DATABASE_URL not set) ---"
  echo "Set DATABASE_URL and run: PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py"
  echo ""
fi

# -----------------------------------------------------------------------------
# Summary (same links as before)
# -----------------------------------------------------------------------------
echo "=============================================="
echo "Deployment complete"
echo "=============================================="
echo ""
echo "API:       $API_URL"
echo "API docs:  $API_URL/docs"
echo "Frontend:  $FRONTEND_SWA_URL"
echo "           (or $FRONTEND_WEBAPP_URL if using App Service for web)"
echo ""
echo "Seeded logins (if seed was run; password: Swan@1234):"
echo "  - demo@example.com"
echo "  - admin@healthforesight.com"
echo "  - sarah.analyst@healthforesight.com"
echo "  - mike.leader@healthforesight.com"
echo "  - jane.exec@healthforesight.com"
echo "  - david.compliance@healthforesight.com"
echo ""
echo "Open the frontend URL above and sign in with email + password."
echo ""
