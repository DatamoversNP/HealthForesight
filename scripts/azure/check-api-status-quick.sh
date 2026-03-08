#!/bin/bash
# Quick check of API status and recent errors

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Checking API status..."
echo ""

# Check app state
echo "1. App Service State:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, defaultHostName:defaultHostName}" \
  --output table

echo ""
echo "2. Testing health endpoint:"
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s -m 10 "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "❌ API is not responding"
    echo ""
    echo "3. Checking environment variables:"
    az webapp config appsettings list \
      --resource-group $RESOURCE_GROUP \
      --name $API_APP_NAME \
      --query "[?name=='CORS_ORIGINS'].{name:name, value:value}" \
      --output table
    
    echo ""
    echo "Please check Azure Portal Log Stream for detailed errors:"
    echo "  https://portal.azure.com/#@/resource/subscriptions/.../providers/Microsoft.Web/sites/$API_APP_NAME/logStream"
fi

