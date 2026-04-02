#!/usr/bin/env bash
# Final deployment: deploy API + Frontend, run migrations, seed users (admin + roles, password Swan@1234).
# Run from repo root. Set DATABASE_URL to your Azure PostgreSQL (or same DB the API uses) to run migrations and seed.
#
# Usage:
#   ./scripts/azure/final-deploy.sh
#   SKIP_SEED=1 ./scripts/azure/final-deploy.sh   # deploy + migrations only
#   SKIP_MIGRATIONS=1 SKIP_SEED=1 ./scripts/azure/final-deploy.sh   # deploy only
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
export API_URL="https://$API_APP_NAME.azurewebsites.net"

echo "=============================================="
echo "HealthForesight – Final deployment"
echo "=============================================="
echo ""
echo "Resource group:  $RESOURCE_GROUP"
echo "API app:         $API_APP_NAME"
echo "Frontend app:    $STATIC_WEB_APP_NAME"
echo "API URL:         $API_URL"
echo ""

# Step 1: Deploy API
echo "--- Step 1: Deploy API ---"
"$SCRIPT_DIR/deploy-api.sh"
echo ""

# Step 2: Deploy Frontend
echo "--- Step 2: Deploy Frontend ---"
"$SCRIPT_DIR/deploy-frontend.sh"
echo ""

# Step 3: Migrations (if DATABASE_URL set and not skipped)
if [ -z "${SKIP_MIGRATIONS}" ] && [ -n "${DATABASE_URL}" ]; then
  echo "--- Step 3: Run database migrations ---"
  cd "$PROJECT_ROOT/apps/api" || exit 1
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  if python3 -m alembic upgrade head 2>/dev/null; then
    echo "Migrations completed."
  else
    echo "Warning: migrations failed or alembic not found. Ensure DATABASE_URL is set and DB is reachable."
  fi
  cd "$PROJECT_ROOT" || exit 1
  echo ""
elif [ -z "${DATABASE_URL}" ]; then
  echo "--- Step 3: Migrations skipped (DATABASE_URL not set) ---"
  echo "To run migrations later: set DATABASE_URL and run: cd apps/api && alembic upgrade head"
  echo ""
fi

# Step 4: Seed users (if DATABASE_URL set and not skipped)
if [ -z "${SKIP_SEED}" ] && [ -n "${DATABASE_URL}" ]; then
  echo "--- Step 4: Seed users (password: Swan@1234) ---"
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  if python3 "$PROJECT_ROOT/scripts/seed_users.py" 2>/dev/null; then
    echo "User seed completed."
  else
    echo "Warning: user seed failed. Run manually: PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py"
  fi
  echo ""
elif [ -z "${DATABASE_URL}" ]; then
  echo "--- Step 4: User seed skipped (DATABASE_URL not set) ---"
  echo "To seed users later, set DATABASE_URL then run:"
  echo "  PYTHONPATH=apps/api/src:packages/common/src python3 scripts/seed_users.py"
  echo ""
fi

echo "=============================================="
echo "Deployment complete"
echo "=============================================="
echo ""
echo "API:       $API_URL"
echo "API docs:  $API_URL/docs"
echo "Frontend:  https://$STATIC_WEB_APP_NAME.azurestaticapps.net (or .azurewebsites.net if using App Service)"
echo ""
echo "Seeded logins (if seed was run; password for all: Swan@1234):"
echo "  - demo@example.com          (Demo User)       – POLICY_ADMIN, UM_LEADER"
echo "  - admin@healthforesight.com (Admin User)     – POLICY_ADMIN"
echo "  - sarah.analyst@healthforesight.com          – ACTUARIAL"
echo "  - mike.leader@healthforesight.com            – UM_LEADER"
echo "  - jane.exec@healthforesight.com              – EXEC_VIEWER"
echo "  - david.compliance@healthforesight.com        – COMPLIANCE"
echo ""
echo "Local login: POST $API_URL/api/v1/auth/login with body: {\"email\": \"...\", \"password\": \"Swan@1234\"}"
echo ""
