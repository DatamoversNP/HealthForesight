#!/bin/bash
# Quick status check - no hanging commands

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Quick Status Check ==="
echo ""

echo "1. Checking if ImagePullFailure is resolved..."
echo "   (Checking recent log entries)"
echo ""

# Get recent logs with timeout
timeout 10 az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -E "ImagePullFailure|Container pull|STARTUP|Application startup|uvicorn|Error" | head -20 || echo "   No recent relevant logs"
echo ""

echo "2. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    RESPONSE=$(curl -s https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "")
    echo "   ✅ SUCCESS! API is working (HTTP $HTTP_CODE)"
    echo "   Response: $RESPONSE"
else
    echo "   ⚠️  Still returning HTTP $HTTP_CODE"
fi
echo ""

echo "3. Checking app state..."
STATE=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query state -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
echo "   App State: $STATE"
echo ""

echo "=== Next Steps ==="
echo ""
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Container is working! Your API is live at:"
    echo "   https://${APP_NAME}.azurewebsites.net"
    echo ""
    echo "To check frontend:"
    echo "   az staticwebapp list --resource-group $RESOURCE_GROUP --query '[].{Name:name, URL:defaultHostname}' -o table"
else
    echo "If still failing:"
    echo "1. Check Azure Portal Log Stream:"
    echo "   https://portal.azure.com → App Services → $APP_NAME → Log stream"
    echo ""
    echo "2. Check Kudu console:"
    echo "   https://${APP_NAME}.scm.azurewebsites.net"
    echo "   Navigate to: LogFiles → Look for latest docker.log"
    echo ""
    echo "3. Look for ImagePullFailure in logs - if it's gone, container is starting"
fi
