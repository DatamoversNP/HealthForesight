#!/bin/bash
# Fix startup to work with Oryx's extraction to /tmp directory

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Oryx Extraction Path Issue ==="
echo ""
echo "Problem: Oryx extracts to /tmp/XXX but startup command expects /home/site/wwwroot"
echo "Solution: Update startup command to use Oryx's extracted location"
echo ""

# Use a simpler startup command that:
# 1. Uses Oryx's generated startup.sh (which handles the paths correctly)
# 2. OR explicitly sets PYTHONPATH to include the extracted location

echo "1. Checking current startup configuration..."
CURRENT_CMD=$(az webapp config show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "linuxFxVersion" -o tsv 2>/dev/null || echo "")

echo "   Current startup: $CURRENT_CMD"
echo ""

echo "2. Updating startup command to use Oryx's startup.sh..."
# Oryx generates /opt/startup/startup.sh which should handle paths correctly
# But we need to ensure it's being used, or we override with a better command

# The key insight: Oryx already sets PYTHONPATH correctly in its startup.sh
# But we need to make sure we're using that file or replicating its logic
STARTUP_CMD="/opt/startup/startup.sh"

echo "   Setting startup to use Oryx's generated script..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command set to use Oryx script"
echo ""

# Actually, wait - the issue is that Oryx's startup.sh might not have the right PYTHONPATH
# Let's check what Oryx actually generates and update it
# Since we can't modify /opt/startup/startup.sh directly, we need a custom command

echo "3. Creating custom startup command that works with Oryx..."
# Use a command that:
# 1. Sources Oryx's environment setup
# 2. Adds extracted directory to PYTHONPATH
# 3. Runs uvicorn

CUSTOM_STARTUP='bash -c "
# Use Oryx\'s generated startup script if it exists, otherwise use custom logic
if [ -f /opt/startup/startup.sh ]; then
    # Oryx startup script should already set up the environment
    # But we may need to add extracted directory to PYTHONPATH
    export PYTHONPATH=\"/tmp/8de57085d2ac8da/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd /tmp/8de57085d2ac8da 2>/dev/null || cd /home/site/wwwroot
    /opt/startup/startup.sh
else
    # Fallback: manual setup
    export PYTHONPATH=\"/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\"
    cd /home/site/wwwroot
    python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}
fi
"'

az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$CUSTOM_STARTUP" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Custom startup command set"
echo ""

echo "4. The real fix: Ensure ZIP structure is correct on next deployment"
echo "   The ZIP should have src/uepi_api/ at the root"
echo "   Oryx will extract it and Python needs to find it"
echo ""

echo "5. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "   Waiting 45 seconds..."
sleep 45

echo ""
echo "6. Testing..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" != "200" ]; then
    echo ""
    echo "   ⚠️  Still not working. The issue is likely the ZIP structure."
    echo "   Next step: Run verify_and_fix_deployment.sh to fix the ZIP"
fi

echo ""
echo "=== Complete ==="
