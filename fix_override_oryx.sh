#!/bin/bash
# Override Oryx's startup script completely

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Overriding Oryx Startup Script ==="
echo ""
echo "Problem: Oryx generates its own startup.sh that doesn't include extracted directory"
echo "Solution: Use a startup command that completely bypasses Oryx's script"
echo ""

# The key: We need to run our own command that finds the extracted directory
# and sets PYTHONPATH BEFORE running uvicorn
# We'll use a startup command that runs directly, not through Oryx's script

STARTUP_CMD='bash -c "
# Find Oryx extracted directory (has antenv and src/uepi_api)
EXTRACTED_DIR=\"\"
for dir in /tmp/*; do
    if [ -d \"\$dir/antenv\" ] && [ -d \"\$dir/src/uepi_api\" ]; then
        EXTRACTED_DIR=\"\$dir\"
        break
    fi
done

# If still not found, try common pattern
if [ -z \"\$EXTRACTED_DIR\" ]; then
    # Look for any /tmp directory with src/uepi_api
    for dir in /tmp/8de* /tmp/*; do
        if [ -d \"\$dir/src/uepi_api\" ] 2>/dev/null; then
            EXTRACTED_DIR=\"\$dir\"
            break
        fi
    done
fi

# Set PYTHONPATH with extracted directory FIRST (highest priority)
if [ -n \"\$EXTRACTED_DIR\" ] && [ -d \"\$EXTRACTED_DIR/src/uepi_api\" ]; then
    export PYTHONPATH=\"\$EXTRACTED_DIR/src:\$EXTRACTED_DIR/packages/common/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd \"\$EXTRACTED_DIR\"
    echo \"[STARTUP] Using extracted directory: \$EXTRACTED_DIR\"
    echo \"[STARTUP] PYTHONPATH: \$PYTHONPATH\"
    echo \"[STARTUP] Current directory: \$(pwd)\"
    echo \"[STARTUP] Checking for uepi_api: \$(ls -la src/uepi_api/main.py 2>&1 | head -1)\"
else
    export PYTHONPATH=\"/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd /home/site/wwwroot
    echo \"[STARTUP] WARNING: Could not find extracted directory, using fallback\"
fi

# Run uvicorn
echo \"[STARTUP] Starting uvicorn...\"
exec python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}
"'

echo "1. Setting startup command to override Oryx..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command set"
echo ""

# Also disable Oryx build if possible (though this might not work)
echo "2. Ensuring app uses our startup command..."
# Check current startup
CURRENT=$(az webapp config show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "linuxFxVersion" -o tsv 2>/dev/null || echo "")
echo "   Current startup: $(echo $CURRENT | cut -c1-100)..."
echo ""

echo "3. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "   Waiting 60 seconds for app to start..."
sleep 60

echo ""
echo "4. Testing health endpoint..."
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
        echo "   Response preview: $(echo "$RESPONSE" | head -3)"
    fi
    echo ""
    echo "   The startup command should now include debug output."
    echo "   Check logs to see the [STARTUP] messages:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
    echo "   Look for lines starting with [STARTUP] to see what directory was found."
fi

echo ""
echo "=== Complete ==="
