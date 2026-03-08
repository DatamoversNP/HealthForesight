#!/bin/bash
# Fix startup - find uepi_api module and set PYTHONPATH correctly

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup - finding uepi_api module..."
echo ""

# Set PYTHONPATH (will be overridden by startup command)
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Startup command that finds uepi_api and sets PYTHONPATH correctly
echo "2. Setting startup command (finds uepi_api module)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'cd /home/site/wwwroot; UEPI_API_DIR=$(find . -type d -name "uepi_api" -path "*/src/uepi_api" 2>/dev/null | head -1 | xargs dirname); if [ -z "$UEPI_API_DIR" ]; then UEPI_API_DIR=$(find . -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname); fi; COMMON_DIR=$(find . -type d -path "*/packages/common/src" 2>/dev/null | head -1); if [ -n "$UEPI_API_DIR" ]; then export PYTHONPATH="$UEPI_API_DIR:${COMMON_DIR}:$PYTHONPATH"; cd "$UEPI_API_DIR"; else export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot; fi; python3 -m pip install --user uvicorn fastapi > /tmp/pip-install.log 2>&1; python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000' \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 90 seconds..."
sleep 90

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
    echo "Check Azure Portal Log Stream"
fi

