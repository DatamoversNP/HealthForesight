#!/bin/bash
# Fix startup - extract output.tar.gz first

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Fixing startup - extracting output.tar.gz first..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Startup command that extracts tar.gz, then finds and runs
echo "2. Setting startup command (extracts tar.gz first)..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file 'cd /home/site/wwwroot && if [ -f "output.tar.gz" ] && [ ! -d "src" ]; then echo "Extracting output.tar.gz..." && tar -xzf output.tar.gz && echo "Extraction complete"; fi && if [ -d "src/uepi_api" ]; then cd src; export PYTHONPATH="$(pwd):$(find /home/site/wwwroot -type d -path "*/packages/common/src" 2>/dev/null | head -1):$PYTHONPATH"; elif [ -d "uepi_api" ]; then export PYTHONPATH="$(pwd):$(find /home/site/wwwroot -type d -path "*/packages/common/src" 2>/dev/null | head -1):$PYTHONPATH"; else UEPI_DIR=$(find . -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname); if [ -n "$UEPI_DIR" ]; then cd "$UEPI_DIR"; export PYTHONPATH="$(pwd):$(find /home/site/wwwroot -type d -path "*/packages/common/src" 2>/dev/null | head -1):$PYTHONPATH"; fi; fi && python3 -m pip install --user uvicorn fastapi > /tmp/pip-install.log 2>&1 && python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000' \
  --output none

# Restart
echo "3. Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

echo ""
echo "✅ Configuration updated. Waiting 120 seconds (extraction takes time)..."
sleep 120

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
    echo "Check Azure Portal Log Stream - look for 'Extraction complete'"
fi

