#!/bin/bash
# Verify and fix CORS configuration

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Current CORS_ORIGINS setting:"
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?name=='CORS_ORIGINS']" \
  --output json

echo ""
echo "Setting CORS_ORIGINS with proper escaping..."
# Use double quotes and escape inner quotes
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    "CORS_ORIGINS=[\"https://gentle-flower-01dffcd0f.2.azurestaticapps.net\",\"https://healthforesight-web-9016.azurestaticapps.net\",\"https://healthforesight-api-9016.azurewebsites.net\",\"http://localhost:3050\",\"http://localhost:3000\"]" \
  --output none

echo ""
echo "Verifying CORS_ORIGINS was set:"
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?name=='CORS_ORIGINS'].value" \
  --output tsv

echo ""
echo "Restarting API..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ Done! Wait 30 seconds, then refresh your frontend."

