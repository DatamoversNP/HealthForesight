#!/bin/bash
# Verify startup command is set correctly and fix if needed

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Verifying startup configuration..."
echo ""

# Check current startup command
echo "1. Current startup command:"
az webapp config show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "appCommandLine" \
  --output tsv

echo ""
echo "2. Setting startup command to 'startup.sh'..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "startup.sh" \
  --output none

echo "✅ Startup command set to 'startup.sh'"
echo ""

# Set PYTHONPATH
echo "3. Setting PYTHONPATH environment variable..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

echo "✅ PYTHONPATH set"
echo ""

# Restart
echo "4. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo "✅ App restarted"
echo ""
echo "Waiting 90 seconds for app to start..."
sleep 90

echo ""
echo "5. Testing API..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s -m 10 "$API_URL/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "API URL: $API_URL"
    echo "API Docs: $API_URL/docs"
else
    echo "⏳ API is still starting or has errors."
    echo ""
    echo "Check Azure Portal Log Stream for details"
fi

