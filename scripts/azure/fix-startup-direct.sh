#!/bin/bash
# Direct fix using uvicorn (simpler approach)

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing API startup with direct uvicorn command..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Use direct uvicorn command (simpler than startup.sh)
# Clean command - no local paths, use Azure paths only
echo "2. Setting startup command to uvicorn (cleaning local paths)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "cd /home/site/wwwroot/src && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000" \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 45 seconds for app to restart..."
sleep 45

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
    echo "Check logs:"
    echo "  az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
    echo ""
    echo "Or run diagnostics:"
    echo "  ./scripts/azure/diagnose-api.sh"
fi

