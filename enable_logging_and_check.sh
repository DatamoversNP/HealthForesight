#!/bin/bash
# Enable logging and check container status

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Enabling Logging and Checking Status ==="
echo ""

echo "1. Enabling application logging..."
az webapp log config \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --application-logging filesystem \
    --docker-container-logging filesystem \
    --level verbose \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Logging enabled"
echo ""

echo "2. Restarting app to generate logs..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""

echo "3. Waiting 30 seconds for logs to generate..."
sleep 30

echo ""
echo "4. Checking logs..."
az webapp log tail \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    2>&1 | grep -v "NotOpenSSLWarning" | head -50

echo ""
echo "5. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ App is working!"
    curl -s https://$APP_NAME.azurewebsites.net/health | head -5
else
    echo "   ⚠️  Still not working (HTTP $HTTP_CODE)"
fi

echo ""
echo "=== Complete ==="
