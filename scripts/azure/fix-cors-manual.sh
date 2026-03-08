#!/bin/bash
# Manual CORS fix - use this if the automated script doesn't work

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Setting CORS_ORIGINS manually..."
echo ""

# Try setting with properly escaped JSON
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    CORS_ORIGINS="[\"https://gentle-flower-01dffcd0f.2.azurestaticapps.net\",\"https://healthforesight-web-9016.azurestaticapps.net\",\"https://healthforesight-api-9016.azurewebsites.net\",\"http://localhost:3050\",\"http://localhost:3000\"]" \
  --output none

echo "✅ CORS_ORIGINS set"
echo ""
echo "Restarting API..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ API restarted"
echo ""
echo "Wait 30 seconds for the API to restart, then refresh your frontend."
echo "The CORS errors should be resolved."

