#!/bin/bash
# Quick status check

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Quick Status Check ==="
echo ""

echo "1. Testing health endpoint..."
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ SUCCESS! App is working!"
    echo "   Response: $RESPONSE"
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
    echo "   ⚠️  HTTP $HTTP_CODE - Container might still be starting"
    echo "   Wait 1-2 more minutes and try again"
else
    echo "   ⚠️  HTTP $HTTP_CODE"
fi

echo ""
echo "2. Checking container config..."
CONFIG=$(az webapp config show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query linuxFxVersion -o tsv 2>/dev/null || echo "")
echo "   Config: $CONFIG"

echo ""
echo "=== Status ==="
echo "If HTTP 503/502: Container is likely still starting (normal, wait 1-2 min)"
echo "If HTTP 200: ✅ App is working!"
echo "If other: Check logs for errors"
