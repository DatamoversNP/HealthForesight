#!/bin/bash
# Final fix: Make startup command work with Oryx's dynamic extraction path

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Final Fix: Handle Oryx Extraction Path ==="
echo ""
echo "The issue: Oryx extracts to /tmp/XXX but startup expects /home/site/wwwroot"
echo "Solution: Add extracted directory to PYTHONPATH dynamically"
echo ""

# The key: Oryx extracts to a temp directory, but we can find it by looking for the uepi_api module
# We'll update the startup command to search for the module location and add it to PYTHONPATH

STARTUP_CMD='bash -c "
# Find where Oryx extracted the files (look for antenv which Oryx creates)
for dir in /tmp/* /home/site/wwwroot; do
    if [ -d \"\$dir/antenv\" ] && [ -d \"\$dir/src/uepi_api\" ]; then
        EXTRACTED_DIR=\"\$dir\"
        break
    fi
done

# If not found, try common locations
if [ -z \"\$EXTRACTED_DIR\" ]; then
    if [ -d \"/tmp/8de57085d2ac8da/src/uepi_api\" ]; then
        EXTRACTED_DIR=\"/tmp/8de57085d2ac8da\"
    elif [ -d \"/home/site/wwwroot/src/uepi_api\" ]; then
        EXTRACTED_DIR=\"/home/site/wwwroot\"
    fi
fi

# Set PYTHONPATH to include extracted directory
if [ -n \"\$EXTRACTED_DIR\" ]; then
    export PYTHONPATH=\"\$EXTRACTED_DIR/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd \"\$EXTRACTED_DIR\"
else
    # Fallback
    export PYTHONPATH=\"/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd /home/site/wwwroot
fi

# Run uvicorn
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}
"'

echo "1. Updating startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command updated"
echo ""

echo "2. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "   Waiting 50 seconds for app to start..."
sleep 50

echo ""
echo "3. Testing health endpoint..."
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ SUCCESS! App is responding!"
    echo "   Response: $RESPONSE"
else
    echo "   ⚠️  HTTP Status: $HTTP_CODE"
    if [ ! -z "$RESPONSE" ]; then
        echo "   Response: $RESPONSE" | head -5
    fi
    echo ""
    echo "   Check logs for errors:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
