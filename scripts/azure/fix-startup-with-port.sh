#!/bin/bash
# Fix startup command using PORT environment variable (Azure standard)

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing API startup with PORT environment variable..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Use PORT environment variable (Azure App Service provides this automatically)
echo "2. Setting startup command with PORT env var..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "cd /home/site/wwwroot/src && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}" \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 60 seconds for app to restart..."
sleep 60

echo ""
echo "4. Testing API..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s -m 10 "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "⏳ API is still starting or has errors."
    echo ""
    echo "Try downloading logs:"
    echo "  az webapp log download --resource-group $RESOURCE_GROUP --name $API_APP_NAME --log-file api-logs.zip"
    echo ""
    echo "Or check in Azure Portal:"
    echo "  https://portal.azure.com -> App Services -> $API_APP_NAME -> Log stream"
fi

