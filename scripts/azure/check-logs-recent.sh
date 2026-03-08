#!/bin/bash
# Check recent logs from Azure App Service

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fetching recent logs (last 50 lines)..."
echo ""

# Get recent logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none 2>&1 | tail -50 || \
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --log-file /tmp/azure-logs.zip 2>&1 && \
  unzip -p /tmp/azure-logs.zip "LogFiles/Application/*.log" 2>/dev/null | tail -50 || \
echo "Unable to fetch logs via CLI. Please check Azure Portal Log Stream."

