#!/bin/bash
# Check API status and get logs via alternative methods

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "=========================================="
echo "API Status Check"
echo "=========================================="
echo ""

# 1. Check app state
echo "1. App Service State:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, kind:kind, defaultHostName:defaultHostName, enabled:enabled, httpsOnly:httpsOnly}" \
  --output table

echo ""
echo "2. Current Startup Command:"
STARTUP_CMD=$(az webapp config show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query appCommandLine \
  --output tsv)
echo "   $STARTUP_CMD"

echo ""
echo "3. Runtime Configuration:"
az webapp config show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{linuxFxVersion:linuxFxVersion, pythonVersion:pythonVersion, alwaysOn:alwaysOn}" \
  --output table

echo ""
echo "4. Critical Environment Variables:"
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[?contains(name, 'AZURE') || contains(name, 'USE_FILE') || contains(name, 'PYTHON') || contains(name, 'PORT')].{name:name, value:value}" \
  --output table

echo ""
echo "5. Recent Deployment Status:"
az webapp deployment list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "[0:3].{id:id, status:status, message:message, active:active, author:author}" \
  --output table

echo ""
echo "6. Test API Endpoint:"
API_URL="https://$API_APP_NAME.azurewebsites.net"
echo "   Testing: $API_URL/api/v1/health"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$API_URL/api/v1/health" 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API is responding (HTTP $HTTP_CODE)"
    curl -s -m 5 "$API_URL/api/v1/health" | head -3
elif [ "$HTTP_CODE" = "000" ]; then
    echo "   ❌ Connection failed (timeout or DNS issue)"
elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "503" ]; then
    echo "   ⚠️  Bad Gateway/Service Unavailable (HTTP $HTTP_CODE) - App may be starting or crashed"
else
    echo "   ⚠️  Unexpected response (HTTP $HTTP_CODE)"
    curl -s -m 5 "$API_URL/api/v1/health" 2>&1 | head -5
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "1. If startup command is empty or wrong, run: ./scripts/azure/fix-startup-direct.sh"
echo "2. Try downloading logs: az webapp log download --resource-group $RESOURCE_GROUP --name $API_APP_NAME --log-file api-logs.zip"
echo "3. Check deployment logs in Azure Portal"
echo "=========================================="

