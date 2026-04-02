#!/usr/bin/env bash
# Fix CORS so the frontend can call the API. Uses Azure App Service CORS (gateway-level)
# so preflight requests get the right headers even before hitting your container.
# Run when you see "No 'Access-Control-Allow-Origin' header" in the browser.
#
# Usage: ./scripts/azure/fix-cors-for-frontend.sh
# Optional: FRONTEND_ORIGIN="https://your-app.azurestaticapps.net" ./scripts/azure/fix-cors-for-frontend.sh
set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-https://healthforesight-web.azurewebsites.net}"

echo "Adding CORS allowed origins at Azure App Service level (gateway)..."
# Include Web App frontend (.azurewebsites.net) and Static Web Apps (.azurestaticapps.net)
ORIGINS_STR="$FRONTEND_ORIGIN https://healthforesight-web.azurestaticapps.net https://proud-glacier-0c52b8e0f.6.azurestaticapps.net https://healthforesight-api.azurewebsites.net http://localhost:3050 http://localhost:3000"
for ORIGIN in $ORIGINS_STR; do
  az webapp cors add \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --allowed-origins "$ORIGIN" \
    --output none 2>/dev/null || true
done
echo "Current CORS origins:"
az webapp cors show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --query allowedOrigins -o tsv 2>/dev/null || true

# Also set app setting so the app code (when it runs) uses the same list
CORS_ORIGINS="${FRONTEND_ORIGIN},https://healthforesight-web.azurestaticapps.net,https://proud-glacier-0c52b8e0f.6.azurestaticapps.net,https://healthforesight-api.azurewebsites.net,http://localhost:3050,http://localhost:3000"
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --settings "CORS_ORIGINS=$CORS_ORIGINS" \
  --output none

echo "Restarting app..."
az webapp restart --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none

echo ""
echo "Done. Wait ~30–60 seconds, then:"
echo "  1. Hard-refresh the frontend (Ctrl+Shift+R or Cmd+Shift+R)."
echo "  2. If the login screen still never appears, clear site data for the frontend URL"
echo "     (DevTools → Application → Storage → Clear site data) so any old token is removed, then reload."
echo "If CORS errors persist, add the origin in Azure Portal:"
echo "  App Service → $API_APP_NAME → API → CORS → add $FRONTEND_ORIGIN"
echo ""
