#!/bin/bash
# Simple fix for Azure deployment - update startup command to handle module path correctly

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Azure Deployment ==="
echo ""

# The issue: Oryx extracts files but PYTHONPATH might not find uepi_api
# Solution: Use a startup command that explicitly sets PYTHONPATH and changes directory

echo "1. Updating startup command..."
# Simplified startup command that works with Oryx build system
STARTUP_CMD='python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}'

az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command updated"
echo ""

echo "2. Ensuring PYTHONPATH is set in app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App settings updated"
echo ""

echo "3. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""

echo "Waiting 30 seconds for app to start..."
sleep 30

echo ""
echo "4. Testing health endpoint..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://$APP_NAME.azurewebsites.net/health || echo "   ⚠️  Could not reach app"

echo ""
echo "=== Fix Complete ==="
echo ""
echo "Next steps:"
echo "1. Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "2. Test health: curl https://$APP_NAME.azurewebsites.net/health"
echo ""
echo "If it still doesn't work, the issue is likely the ZIP structure."
echo "The ZIP needs to have src/uepi_api/ at the root level."
