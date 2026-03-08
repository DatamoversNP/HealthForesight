#!/bin/bash
# Check detailed logs to see what's happening

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Detailed Logs ==="
echo ""
echo "Getting last 50 lines of logs..."
echo ""

az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  2>&1 | grep -v "NotOpenSSLWarning" | tail -50

echo ""
echo "=== Checking for specific issues ==="
echo ""

echo "1. Looking for [STARTUP] messages (should appear if our startup.sh ran):"
az webapp log download \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file /tmp/logs.zip \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

if [ -f /tmp/logs.zip ]; then
    unzip -q /tmp/logs.zip -d /tmp/logs_extracted 2>/dev/null || true
    if [ -d /tmp/logs_extracted ]; then
        echo "   Searching for [STARTUP] in logs..."
        grep -r "\[STARTUP\]" /tmp/logs_extracted 2>/dev/null | head -10 || echo "   No [STARTUP] messages found"
        
        echo ""
        echo "2. Looking for ModuleNotFoundError:"
        grep -r "ModuleNotFoundError" /tmp/logs_extracted 2>/dev/null | head -5 || echo "   No ModuleNotFoundError found"
        
        echo ""
        echo "3. Looking for uvicorn startup:"
        grep -r "uvicorn\|Starting" /tmp/logs_extracted 2>/dev/null | tail -5 || echo "   No uvicorn messages"
    fi
    rm -rf /tmp/logs_extracted /tmp/logs.zip 2>/dev/null || true
fi

echo ""
echo "=== Test Health Endpoint ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ App is working!"
    curl -s https://$APP_NAME.azurewebsites.net/health
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
    echo "⚠️  App is starting or unavailable"
else
    echo "❌ App has errors"
fi
