#!/bin/bash
# Set startup command directly as a bash one-liner that Oryx will execute

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Setting Direct Startup Command ==="
echo ""
echo "This will set a startup command that directly finds the extracted directory"
echo "and sets PYTHONPATH, bypassing Oryx's generated script"
echo ""

# Create a startup command that:
# 1. Finds the Oryx extracted directory
# 2. Adds it to PYTHONPATH
# 3. Runs uvicorn
# All in one command that Oryx will execute

STARTUP_CMD='bash -c "for d in /tmp/*; do [ -d \"$d/antenv\" ] && [ -d \"$d/src/uepi_api\" ] && export PYTHONPATH=\"$d/src:$d/packages/common/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH\" && cd \"$d\" && break; done; python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"'

echo "1. Setting startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command set"
echo ""

echo "2. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "   Waiting 60 seconds for app to start..."
sleep 60

echo ""
echo "3. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ SUCCESS! App is responding!"
    echo "   Response: $RESPONSE"
    echo ""
    echo "🎉 Deployment is working!"
else
    echo "   ⚠️  HTTP Status: $HTTP_CODE"
    if [ ! -z "$RESPONSE" ]; then
        echo "   Response: $(echo "$RESPONSE" | head -3)"
    fi
    echo ""
    echo "   Check logs:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
