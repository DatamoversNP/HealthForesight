#!/bin/bash
# Final fix: Set PYTHONPATH in app settings so Oryx includes extracted directory
# Also ensure startup.sh finds and uses the extracted directory

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Final PYTHONPATH Fix ==="
echo ""
echo "Setting PYTHONPATH to include wildcard pattern that Oryx can use"
echo ""

# The key insight: We need to set PYTHONPATH in a way that works with Oryx
# Oryx extracts to /tmp/XXX, so we'll update app settings to include that pattern
# But actually, Oryx sets PYTHONPATH itself, so we need to modify our startup.sh
# to override it AFTER Oryx sets it

echo "1. Updating PYTHONPATH in app settings..."
# Set PYTHONPATH with both wwwroot and a note about extracted dir
# Oryx will prepend its paths, but our startup.sh will add the extracted dir
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App settings updated"
echo ""

echo "2. The real fix: startup.sh needs to modify PYTHONPATH after Oryx sets it"
echo "   Our startup.sh should add /tmp/XXX/src to PYTHONPATH at runtime"
echo ""

echo "3. Verifying startup.sh in apps/api has the fix..."
if [ -f "apps/api/startup.sh" ]; then
    if grep -q "EXTRACTED_DIR" apps/api/startup.sh; then
        echo "   ✅ startup.sh has the fix"
        echo "   Key parts:"
        grep -A 2 "EXTRACTED_DIR" apps/api/startup.sh | head -5
    else
        echo "   ❌ startup.sh does NOT have the fix!"
        echo "   Need to recreate it"
    fi
else
    echo "   ❌ startup.sh not found!"
fi

echo ""
echo "4. Testing health endpoint to see current state..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ App is working!"
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
    echo "   ⚠️  App is still starting or has issues"
else
    echo "   ⚠️  App has errors"
fi

echo ""
echo "=== Next Steps ==="
echo ""
echo "If app is still not working, check logs for:"
echo "  1. [STARTUP] messages - shows if our startup.sh ran"
echo "  2. ModuleNotFoundError - shows if PYTHONPATH still wrong"
echo ""
echo "Run: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "If you see ModuleNotFoundError but NO [STARTUP] messages,"
echo "then our startup.sh isn't being executed. Need to check why."
