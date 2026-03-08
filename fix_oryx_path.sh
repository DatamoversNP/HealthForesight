#!/bin/bash
# Fix: Add Oryx's extracted directory to PYTHONPATH

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Oryx Path Issue ==="
echo ""
echo "Problem: Oryx extracts to /tmp/XXX/src but PYTHONPATH doesn't include it"
echo "Solution: Update startup command to add extracted directory to PYTHONPATH"
echo ""

# The key: Oryx extracts to /tmp/XXX and we need to add /tmp/XXX/src to PYTHONPATH
# We'll create a startup command that finds the extracted directory and adds it

STARTUP_CMD='bash -c "
# Oryx extracts to a temp directory like /tmp/8de5728c28bbf35
# Find the directory with antenv (Oryx creates this)
EXTRACTED_DIR=\"\"
for dir in /tmp/*; do
    if [ -d \"\$dir/antenv\" ] && [ -d \"\$dir/src/uepi_api\" ]; then
        EXTRACTED_DIR=\"\$dir\"
        break
    fi
done

# If not found, try the specific one from logs
if [ -z \"\$EXTRACTED_DIR\" ] && [ -d \"/tmp/8de5728c28bbf35/src/uepi_api\" ]; then
    EXTRACTED_DIR=\"/tmp/8de5728c28bbf35\"
fi

# Set PYTHONPATH - include extracted directory FIRST so it takes precedence
if [ -n \"\$EXTRACTED_DIR\" ]; then
    export PYTHONPATH=\"\$EXTRACTED_DIR/src:\$EXTRACTED_DIR/packages/common/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd \"\$EXTRACTED_DIR\"
    echo \"Using extracted directory: \$EXTRACTED_DIR\"
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
    echo "   Check logs:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
