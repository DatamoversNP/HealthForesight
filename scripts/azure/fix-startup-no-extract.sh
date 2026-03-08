#!/bin/bash
# Fix startup command - no extraction needed (Azure extracts zip automatically)

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup command (no extraction)..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH environment variable..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Set startup command (Azure already extracted the zip, no need to extract tar.gz)
echo "2. Setting startup command (finds code in wwwroot, no extraction)..."
STARTUP_CMD='cd /home/site/wwwroot && \
UEPI_DIR=$(find . -maxdepth 3 -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname); \
COMMON_DIR=$(find . -maxdepth 3 -type d -path "*/packages/common/src" 2>/dev/null | head -1); \
if [ -n "$UEPI_DIR" ] && [ -d "$UEPI_DIR/uepi_api" ]; then \
    echo "Found uepi_api at: $UEPI_DIR"; \
    export PYTHONPATH="$UEPI_DIR:${COMMON_DIR}:$PYTHONPATH"; \
    cd "$UEPI_DIR"; \
elif [ -d "src/uepi_api" ]; then \
    echo "Using src/uepi_api"; \
    export PYTHONPATH="/home/site/wwwroot/src:${COMMON_DIR}:$PYTHONPATH"; \
    cd src; \
else \
    echo "Using fallback paths"; \
    export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"; \
    cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot; \
fi; \
# Use Oryx virtual environment Python if available, otherwise system Python
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then \
    PYTHON_CMD="/home/site/wwwroot/antenv/bin/python"; \
    echo "Using Oryx virtual environment Python"; \
elif [ -f "/home/site/wwwroot/antenv/bin/python3" ]; then \
    PYTHON_CMD="/home/site/wwwroot/antenv/bin/python3"; \
    echo "Using Oryx virtual environment Python3"; \
else \
    PYTHON_CMD="python3"; \
    echo "Using system Python3, installing dependencies..."; \
    REQ_FILE=$(find . -name "requirements.txt" 2>/dev/null | head -1); \
    if [ -n "$REQ_FILE" ]; then \
        python3 -m pip install --user -r "$REQ_FILE" > /tmp/pip-install.log 2>&1; \
    else \
        python3 -m pip install --user uvicorn fastapi pydantic pydantic-settings > /tmp/pip-install.log 2>&1; \
    fi; \
fi; \
echo "Starting uvicorn with PYTHONPATH=$PYTHONPATH using $PYTHON_CMD"; \
$PYTHON_CMD -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000'

az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "$STARTUP_CMD" \
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
    echo "Check Azure Portal Log Stream for details"
fi

