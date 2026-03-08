#!/bin/bash
# Check API logs and diagnose issues

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "=========================================="
echo "API Diagnostics"
echo "=========================================="
echo ""

# Check app state
echo "1. App Service State:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, kind:kind, defaultHostName:defaultHostName}" \
  --output table

echo ""
echo "2. Startup Configuration:"
az webapp config show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{runtime:linuxFxVersion, startupCommand:appCommandLine, alwaysOn:alwaysOn}" \
  --output table

echo ""
echo "3. Environment Variables (Azure File Storage):"
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?contains(name, 'AZURE') || contains(name, 'USE_FILE')].{name:name, value:value}" \
  --output table

echo ""
echo "4. Recent Logs (last 50 lines):"
echo "   (Press Ctrl+C to exit log viewer)"
echo ""
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output table

