#!/bin/bash
# View API logs in real-time

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "=========================================="
echo "API Logs - Press Ctrl+C to exit"
echo "=========================================="
echo ""
echo "App: $API_APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""
echo "Recent logs (last 100 lines):"
echo ""

# Get recent logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output table

