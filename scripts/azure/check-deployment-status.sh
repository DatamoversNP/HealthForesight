#!/bin/bash
# Check Azure deployment status

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Checking deployment status..."
echo ""

# Check app status
echo "App Service Status:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, defaultHostName:defaultHostName, kind:kind}" \
  --output table

echo ""
echo "Recent deployments:"
az webapp deployment list-publishing-profiles \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --xml 2>/dev/null | head -20 || echo "Deployment info not available via CLI"

echo ""
echo "Checking if API is responding..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "⏳ API is not responding yet (deployment may still be in progress)"
    echo ""
    echo "Check logs:"
    echo "  az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
fi

