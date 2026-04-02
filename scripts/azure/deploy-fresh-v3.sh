#!/usr/bin/env bash
# Deploy HealthForesight v3 (API + frontend) to the fresh v3 Azure resources.
# Uses v3 resource group and app names so the existing deployment is NOT disturbed.
# Run from repo root: ./scripts/azure/deploy-fresh-v3.sh
# Prerequisite: run provision-fresh-v3.sh first (or have v3 resources already created).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-v3-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api-v3}"
export STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web-v3}"
export API_URL="https://$API_APP_NAME.azurewebsites.net"

echo "=============================================="
echo "HealthForesight v3 – Deploy API + Frontend"
echo "=============================================="
echo ""
echo "Resource group:  $RESOURCE_GROUP"
echo "API app:         $API_APP_NAME"
echo "Static web app:  $STATIC_WEB_APP_NAME"
echo "API URL:         $API_URL"
echo ""

cd "$PROJECT_ROOT" || exit 1

echo "--- Deploying API ---"
"$SCRIPT_DIR/deploy-api.sh"

echo ""
echo "--- Deploying Frontend ---"
"$SCRIPT_DIR/deploy-frontend.sh"

echo ""
echo "=============================================="
echo "v3 deployment complete"
echo "=============================================="
echo ""
echo "API:      $API_URL"
echo "API docs: $API_URL/docs"
echo "Web:      https://$STATIC_WEB_APP_NAME.azurestaticapps.net"
echo ""
echo "Quick test: curl -s $API_URL/api/v1/health"
echo ""
