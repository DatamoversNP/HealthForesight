#!/bin/bash
# Set CORS using JSON file (more reliable)

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Setting CORS_ORIGINS using JSON file..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings @${SCRIPT_DIR}/cors-settings.json \
  --output none

echo "✅ CORS_ORIGINS set"
echo ""
echo "Verifying..."
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?name=='CORS_ORIGINS'].{name:name, value:value}" \
  --output table

echo ""
echo "Restarting API..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ API restarted"
echo ""
echo "Wait 30 seconds, then refresh your frontend."

