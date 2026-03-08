#!/bin/bash
# Simple startup - install uvicorn to system Python

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Simple startup fix - install uvicorn to system Python..."
echo ""

# Set PYTHONPATH
echo "1. Setting PYTHONPATH..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

# Simple startup: install uvicorn if needed, then run
echo "2. Setting simple startup command..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "cd /home/site/wwwroot/src && python3 -m pip install --user uvicorn fastapi > /dev/null 2>&1; python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000" \
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

