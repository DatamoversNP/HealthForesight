#!/bin/bash
# Comprehensive API diagnostics

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "=========================================="
echo "API Diagnostics"
echo "=========================================="
echo ""

# 1. Check app state
echo "1. App Service State:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, kind:kind, defaultHostName:defaultHostName, enabled:enabled}" \
  --output table

echo ""
echo "2. Startup Configuration:"
az webapp config show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{runtime:linuxFxVersion, startupCommand:appCommandLine, alwaysOn:alwaysOn}" \
  --output table

echo ""
echo "3. Environment Variables (Critical):"
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?contains(name, 'AZURE') || contains(name, 'USE_FILE') || contains(name, 'PYTHON')].{name:name, value:value}" \
  --output table

echo ""
echo "4. Recent Logs (last 50 lines):"
echo "   (This will show the last 50 lines of logs)"
echo ""
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --log-file /tmp/api-logs.zip 2>/dev/null || echo "Could not download logs"

if [ -f /tmp/api-logs.zip ]; then
    unzip -p /tmp/api-logs.zip "LogFiles/Application/*.log" 2>/dev/null | tail -50 || \
    unzip -p /tmp/api-logs.zip "*.log" 2>/dev/null | tail -50 || \
    echo "Could not extract logs from zip"
    rm -f /tmp/api-logs.zip
fi

echo ""
echo "5. Test API Endpoint:"
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s -m 5 "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    curl -s "$API_URL/api/v1/health" | head -5
else
    echo "❌ API is not responding"
    echo "   URL: $API_URL/api/v1/health"
    echo "   Error: $(curl -s -m 5 "$API_URL/api/v1/health" 2>&1 | head -3)"
fi

echo ""
echo "=========================================="
echo "For real-time logs, run:"
echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo "=========================================="

