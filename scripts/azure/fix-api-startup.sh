#!/bin/bash
# Fix API startup configuration

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing API startup configuration..."
echo ""

# Set PYTHONPATH (startup.sh will override this, but set it as fallback)
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Update startup command - use startup.sh which handles Azure Oryx build system
echo "2. Updating startup command..."
# Use the startup.sh script that handles Azure's Oryx extraction and sets up PYTHONPATH correctly
# The script should be in the root of the deployment
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "bash startup.sh" \
  --output none

# Restart the app
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 30 seconds for app to restart..."
sleep 30

echo ""
echo "4. Testing API..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "⏳ API is still starting. Check logs:"
    echo "  az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
fi

