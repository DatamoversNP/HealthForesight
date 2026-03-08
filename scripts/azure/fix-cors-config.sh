#!/bin/bash
# Fix CORS_ORIGINS environment variable in Azure

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing CORS_ORIGINS configuration..."
echo ""

# Set CORS_ORIGINS to a valid JSON array or remove it to use defaults
echo "Setting CORS_ORIGINS to valid JSON array..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    CORS_ORIGINS='["https://healthforesight-api-9016.azurewebsites.net","http://localhost:3050","http://localhost:3000"]' \
  --output none

echo "✅ CORS_ORIGINS set"
echo ""

# Restart app
echo "Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ App restarted"
echo ""
echo "Waiting 60 seconds for app to start..."
sleep 60

echo ""
echo "Testing API..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s -m 10 "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "⏳ API is still starting or has errors."
    echo ""
    echo "Check Azure Portal Log Stream for details"
fi

