#!/bin/bash
# Check Docker container logs

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Docker Container Logs ==="
echo ""

echo "1. Checking app state..."
APP_STATE=$(az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state -o tsv 2>/dev/null || echo "unknown")
echo "   App State: $APP_STATE"
echo ""

echo "2. Streaming logs (press Ctrl+C to stop)..."
echo ""
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  2>&1 | grep -v "NotOpenSSLWarning" | head -100

echo ""
echo ""
echo "3. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ App is working!"
    curl -s https://$APP_NAME.azurewebsites.net/health
else
    echo "   ⚠️  App not responding yet (HTTP $HTTP_CODE)"
    echo "   This might be normal - Docker containers can take 2-3 minutes to start"
fi
