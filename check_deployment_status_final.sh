#!/bin/bash
# Check deployment status and test if app is working

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Deployment Status ==="
echo ""

echo "1. Waiting 30 seconds for deployment to complete..."
sleep 30

echo ""
echo "2. Checking deployment status..."
az webapp deployment list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query '[0].{Status:status,Time:active_time,Message:message}' -o table 2>&1 | grep -v "NotOpenSSLWarning" || echo "   Could not get deployment status"

echo ""
echo "3. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ SUCCESS! App is responding!"
    echo "   Response: $RESPONSE"
    echo ""
    echo "🎉 Deployment is working!"
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
    echo "   ⚠️  HTTP $HTTP_CODE - App might still be starting"
    echo "   Wait a bit more and try again"
else
    echo "   ⚠️  HTTP Status: $HTTP_CODE"
    if [ ! -z "$RESPONSE" ]; then
        echo "   Response: $(echo "$RESPONSE" | head -3)"
    fi
fi

echo ""
echo "4. Checking recent logs for [STARTUP] messages..."
echo ""
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  2>&1 | grep -E "\[STARTUP\]|ModuleNotFoundError|Traceback|Starting uvicorn|Using extracted directory" | tail -20 || echo "   Could not stream logs (app might still be starting)"

echo ""
echo "=== Status Check Complete ==="
echo ""
echo "If app is not working, check full logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "Look for [STARTUP] messages to see if the fix is working."
