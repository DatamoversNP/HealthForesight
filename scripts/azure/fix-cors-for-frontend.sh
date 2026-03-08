#!/bin/bash
# Fix CORS to allow frontend Static Web App

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web-9016}"

echo "Fixing CORS configuration to allow frontend..."
echo ""

# Get the actual Static Web App URL (it might be different from the name)
STATIC_WEB_URL=$(az staticwebapp show \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "defaultHostname" \
  --output tsv 2>/dev/null || echo "")

if [ -z "$STATIC_WEB_URL" ]; then
    # Fallback: construct URL from name
    STATIC_WEB_URL="https://${STATIC_WEB_APP_NAME}.azurestaticapps.net"
    echo "⚠️  Could not get Static Web App URL, using: $STATIC_WEB_URL"
else
    STATIC_WEB_URL="https://${STATIC_WEB_URL}"
    echo "✅ Found Static Web App URL: $STATIC_WEB_URL"
fi

# Also check for the actual deployed URL (gentle-flower-01dffcd0f.2.azurestaticapps.net)
# This might be different from the resource name
ACTUAL_FRONTEND_URL="https://gentle-flower-01dffcd0f.2.azurestaticapps.net"

echo ""
echo "Setting CORS_ORIGINS to include:"
echo "  - $STATIC_WEB_URL"
echo "  - $ACTUAL_FRONTEND_URL"
echo "  - https://$API_APP_NAME.azurewebsites.net"
echo ""

# Set CORS_ORIGINS as JSON array
CORS_ORIGINS_JSON="[\"$STATIC_WEB_URL\",\"$ACTUAL_FRONTEND_URL\",\"https://$API_APP_NAME.azurewebsites.net\",\"http://localhost:3050\",\"http://localhost:3000\"]"

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    CORS_ORIGINS="$CORS_ORIGINS_JSON" \
  --output none

echo "✅ CORS_ORIGINS updated"
echo ""

# Restart app to apply changes
echo "Restarting API app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ API app restarted"
echo ""
echo "Waiting 30 seconds for app to restart..."
sleep 30

echo ""
echo "Testing API CORS..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
# Test with OPTIONS request (preflight)
if curl -X OPTIONS -H "Origin: $ACTUAL_FRONTEND_URL" -H "Access-Control-Request-Method: GET" \
   -v "$API_URL/api/v1/health" 2>&1 | grep -q "access-control-allow-origin"; then
    echo "✅ CORS is working!"
else
    echo "⏳ CORS might still be configuring. Check the API logs if issues persist."
fi

echo ""
echo "Frontend URL: $ACTUAL_FRONTEND_URL"
echo "API URL: $API_URL"

