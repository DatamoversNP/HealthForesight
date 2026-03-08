#!/bin/bash
# Final fix - handle Oryx extraction and virtual environment

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Final startup fix - handling Oryx extraction..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Create a startup command that:
# 1. Finds Oryx-extracted directory (if exists)
# 2. Uses its virtual environment Python
# 3. Falls back to installing uvicorn if needed
echo "2. Setting startup command (handles all cases)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'EXTRACTED=$(find /tmp -maxdepth 1 -type d -name "8de*" 2>/dev/null | head -1); PYTHON_CMD="python"; if [ -n "$EXTRACTED" ] && [ -d "$EXTRACTED/antenv/bin/python" ]; then PYTHON_CMD="$EXTRACTED/antenv/bin/python"; cd "$EXTRACTED/src"; export PYTHONPATH="$EXTRACTED/src:$EXTRACTED/packages/common/src:$PYTHONPATH"; elif [ -d "/home/site/wwwroot/antenv/bin/python" ]; then PYTHON_CMD="/home/site/wwwroot/antenv/bin/python"; cd /home/site/wwwroot/src; export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; else cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot; export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; if ! python -c "import uvicorn" 2>/dev/null; then pip install uvicorn fastapi 2>&1 | head -5; fi; fi; $PYTHON_CMD -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}' \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 90 seconds for app to restart..."
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
    echo "Check Azure Portal Log Stream for detailed errors"
fi

