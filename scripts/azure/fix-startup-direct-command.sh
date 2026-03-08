#!/bin/bash
# Fix startup using direct command (bypass startup.sh)

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup with direct command (bypassing startup.sh)..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Use direct command - Oryx will handle the environment
# Find Oryx extracted dir and use it, or fallback to wwwroot
echo "2. Setting startup command (direct, handles Oryx)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'EXTRACTED_DIR=$(find /tmp -maxdepth 1 -type d -name "8de*" 2>/dev/null | head -1); if [ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR/src/uepi_api" ]; then cd "$EXTRACTED_DIR" && export PYTHONPATH="$EXTRACTED_DIR/src:$EXTRACTED_DIR/packages/common/src:$PYTHONPATH" && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}; else cd /home/site/wwwroot/src && export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH" && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi' \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 60 seconds for app to restart..."
sleep 60

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
    echo "Check logs in Azure Portal Log Stream"
fi

