#!/bin/bash
# Check startup errors from Azure App Service logs

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Checking recent logs for startup errors..."
echo ""

# Try to get logs via log stream (last 100 lines)
echo "Attempting to fetch logs..."
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none 2>&1 | tail -100 || echo "Could not fetch logs via tail"

echo ""
echo "Alternative: Check logs in Azure Portal:"
echo "  https://portal.azure.com/#@/resource/subscriptions/.../providers/Microsoft.Web/sites/$API_APP_NAME/logStream"
echo ""
echo "Or download logs:"
echo "  az webapp log download --resource-group $RESOURCE_GROUP --name $API_APP_NAME --log-file /tmp/azure-logs.zip"

