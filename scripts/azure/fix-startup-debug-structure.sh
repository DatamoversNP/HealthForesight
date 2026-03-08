#!/bin/bash
# Fix startup - debug directory structure first

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup - with directory structure debugging..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Startup command that lists structure, then finds and runs
echo "2. Setting startup command (with debugging)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'cd /home/site/wwwroot && echo "=== Directory structure ===" && ls -la && echo "=== Looking for uepi_api ===" && find . -name "uepi_api" -type d 2>/dev/null | head -5 && echo "=== Looking for main.py ===" && find . -name "main.py" -path "*/uepi_api/main.py" 2>/dev/null | head -3 && UEPI_PATH=$(find . -name "main.py" -path "*/uepi_api/main.py" 2>/dev/null | head -1 | sed "s|/uepi_api/main.py||"); if [ -n "$UEPI_PATH" ]; then echo "Found uepi_api at: $UEPI_PATH" && cd "$UEPI_PATH" && export PYTHONPATH="$(pwd):$(find /home/site/wwwroot -type d -path "*/packages/common/src" 2>/dev/null | head -1):$PYTHONPATH" && echo "PYTHONPATH: $PYTHONPATH"; else echo "Using fallback paths" && export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; fi; python3 -m pip install --user uvicorn fastapi > /tmp/pip-install.log 2>&1; python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000' \
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
    echo "Check Azure Portal Log Stream - look for '=== Directory structure ===' to see what's actually there"
fi

