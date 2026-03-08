#!/bin/bash
# Fix startup - ensure pip and python use same interpreter

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup - ensuring pip and python use same interpreter..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Create startup command that:
# 1. Finds Oryx-extracted directory
# 2. Uses its Python, or installs uvicorn to system Python and uses that
echo "2. Setting startup command (fixes pip/python mismatch)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'EXTRACTED=$(find /tmp -maxdepth 1 -type d -name "8de*" 2>/dev/null | head -1); if [ -n "$EXTRACTED" ] && [ -d "$EXTRACTED/antenv/bin/python" ] && [ -d "$EXTRACTED/src/uepi_api" ]; then cd "$EXTRACTED/src" && export PYTHONPATH="$EXTRACTED/src:$EXTRACTED/packages/common/src:$PYTHONPATH" && "$EXTRACTED/antenv/bin/python" -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}; elif [ -d "/home/site/wwwroot/antenv/bin/python" ] && [ -d "/home/site/wwwroot/src/uepi_api" ]; then cd /home/site/wwwroot/src && export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH" && "/home/site/wwwroot/antenv/bin/python" -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}; else cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot; export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; PYTHON_CMD=$(which python3 || which python); if ! $PYTHON_CMD -c "import uvicorn" 2>/dev/null; then $PYTHON_CMD -m pip install --user uvicorn fastapi 2>&1 | head -10; fi; $PYTHON_CMD -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi' \
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

