#!/usr/bin/env bash
# Redeploy HealthForesight to the EXISTING Azure apps (overwrites current deployment).
# Uses: healthforesight-rg, healthforesight-api-9016, healthforesight-web-9016
# Run from repo root: ./scripts/azure/redeploy-existing.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Existing deployment – overwrite these apps
export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
export API_URL="https://$API_APP_NAME.azurewebsites.net"

echo "=============================================="
echo "Redeploy to existing Azure apps (overwrite)"
echo "=============================================="
echo ""
echo "Resource group:  $RESOURCE_GROUP"
echo "API app:         $API_APP_NAME"
echo "Static web app:  $STATIC_WEB_APP_NAME"
echo ""

# Check that the API web app exists (avoid cryptic ResourceNotFound)
if ! az webapp show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none 2>/dev/null; then
  echo "The API app '$API_APP_NAME' was not found in resource group '$RESOURCE_GROUP'."
  echo ""
  echo "Either:"
  echo "  1. Create the app first (e.g. run: ./scripts/azure/provision-fresh-v3.sh for a new v3 deployment)"
  echo "  2. Or set the correct names: export RESOURCE_GROUP=... API_APP_NAME=... STATIC_WEB_APP_NAME=..."
  echo ""
  echo "List your web apps: az webapp list --resource-group $RESOURCE_GROUP --query '[].name' -o tsv"
  exit 1
fi

cd "$PROJECT_ROOT" || exit 1

echo "--- Deploying API (overwrites existing) ---"
"$SCRIPT_DIR/deploy-api.sh"

echo ""
echo "--- Deploying Frontend (overwrites existing) ---"
"$SCRIPT_DIR/deploy-frontend.sh"

echo ""
echo "=============================================="
echo "Redeploy complete"
echo "=============================================="
echo ""
echo "API:      $API_URL"
echo "Web:      https://$STATIC_WEB_APP_NAME.azurestaticapps.net"
echo ""
