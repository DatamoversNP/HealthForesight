#!/bin/bash
# Fix the startup command to work with Oryx's extraction mechanism

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Startup Command ==="
echo ""

# The issue: Oryx extracts files to /tmp/XXX but PYTHONPATH points to /home/site/wwwroot
# Solution: Use a startup command that dynamically adds the extracted directory to PYTHONPATH

echo "1. Updating startup command to handle Oryx extraction..."
echo ""

# Create a startup command that:
# 1. Finds where Oryx extracted files (usually /tmp/XXX or /home/site/wwwroot)
# 2. Adds both locations to PYTHONPATH
# 3. Changes to the appropriate directory
# 4. Runs uvicorn

STARTUP_CMD='bash -c "
# Find extracted directory (Oryx usually extracts to /tmp or uses /home/site/wwwroot)
EXTRACTED_DIR=\"/tmp/8de57085d2ac8da\"
WWWROOT_DIR=\"/home/site/wwwroot\"

# Try to find where src/uepi_api actually is
if [ -d \"\$EXTRACTED_DIR/src/uepi_api\" ]; then
    SRC_DIR=\"\$EXTRACTED_DIR/src\"
    cd \"\$EXTRACTED_DIR\"
elif [ -d \"\$WWWROOT_DIR/src/uepi_api\" ]; then
    SRC_DIR=\"\$WWWROOT_DIR/src\"
    cd \"\$WWWROOT_DIR\"
else
    # Search for uepi_api module
    for dir in /tmp/* /home/site/wwwroot; do
        if [ -d \"\$dir/src/uepi_api\" ]; then
            SRC_DIR=\"\$dir/src\"
            cd \"\$dir\"
            break
        fi
    done
fi

# Set PYTHONPATH to include found location
export PYTHONPATH=\"\$SRC_DIR:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"

# Run uvicorn
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}
"'

# Set the startup command
echo "   Setting startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command updated"
echo ""

# Also ensure PYTHONPATH includes common paths
echo "2. Updating PYTHONPATH in app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ PYTHONPATH configured"
echo ""

# Restart the app
echo "3. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "   Waiting 45 seconds for app to start..."
sleep 45

# Test
echo ""
echo "4. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ App is responding! HTTP $HTTP_CODE"
    curl -s https://$APP_NAME.azurewebsites.net/health | head -100
else
    echo "   ⚠️  App returned HTTP $HTTP_CODE"
    echo ""
    echo "   Check logs:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
