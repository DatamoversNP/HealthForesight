#!/bin/bash
# Check deployment structure and fix module path issues

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking and Fixing Deployment ==="
echo ""

# First, set PYTHONPATH in app settings
echo "1. Setting PYTHONPATH in app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

echo "   ✅ PYTHONPATH set"
echo ""

# Update startup command - Azure App Service Python runtime uses PYTHONPATH automatically
echo "2. Updating startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}" \
  --output none

echo "   ✅ Startup command updated"
echo ""

# Verify app settings
echo "3. Verifying app settings..."
az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='PYTHONPATH'].{Name:name, Value:value}" -o table

echo ""

# Restart app
echo "4. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none

echo "   ✅ App restarted"
echo ""
echo "Waiting 20 seconds for app to start..."
sleep 20

echo ""
echo "=== Testing ==="
echo "Testing health endpoint..."
curl -s https://$APP_NAME.azurewebsites.net/health | head -10

echo ""
echo ""
echo "=== Next Steps ==="
echo "If still getting errors, check:"
echo "1. Kudu console: https://$APP_NAME.scm.azurewebsites.net"
echo "2. Verify files: cd /home/site/wwwroot && ls -la src/uepi_api/"
echo "3. Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
