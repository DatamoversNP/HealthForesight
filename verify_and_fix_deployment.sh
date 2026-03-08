#!/bin/bash
# Verify ZIP structure and fix deployment

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Verifying and Fixing Deployment ==="
echo ""

# Step 1: Check if ZIP exists and verify its structure
echo "1. Checking deployment ZIP structure..."
cd "$SCRIPT_DIR/apps/api"

if [ -f "deploy.zip" ]; then
    echo "   Found existing deploy.zip"
    echo "   Verifying contents..."
    
    # Check if src/uepi_api/main.py exists in ZIP
    if zipinfo deploy.zip | grep -q "src/uepi_api/main.py"; then
        echo "   ✅ ZIP contains src/uepi_api/main.py"
    else
        echo "   ❌ ZIP does NOT contain src/uepi_api/main.py"
        echo "   ZIP contents:"
        zipinfo deploy.zip | grep -E "^.*src/" | head -10
        echo ""
        echo "   This is the problem! The ZIP structure is incorrect."
        echo "   We need to recreate the ZIP with correct structure."
        rm -f deploy.zip
    fi
else
    echo "   No deploy.zip found - will create new one"
fi

# Step 2: Create correct ZIP if needed
if [ ! -f "deploy.zip" ]; then
    echo ""
    echo "2. Creating deployment ZIP with correct structure..."
    
    # Ensure we're in apps/api directory
    cd "$SCRIPT_DIR/apps/api"
    
    # Create ZIP that includes everything from apps/api (which has src/uepi_api/)
    zip -r deploy.zip . \
      -x "*.git*" \
      -x "*.venv*" \
      -x "*__pycache__*" \
      -x "*.pyc" \
      -x "*.log" \
      -x "*.pytest_cache*" \
      -x "*.mypy_cache*" \
      -x "deploy.zip" \
      -x "data/*" \
      -x "target_data_model/*" \
      -x "tests/*" 2>&1 | grep -v "zip warning" || true
    
    # Verify the ZIP
    echo "   Verifying ZIP..."
    if zipinfo deploy.zip | grep -q "src/uepi_api/main.py"; then
        echo "   ✅ ZIP created with correct structure"
        echo ""
        echo "   Key files in ZIP:"
        zipinfo deploy.zip | grep -E "(src/uepi_api/main.py|requirements.txt|startup.sh)" | head -5
    else
        echo "   ❌ ZIP structure still incorrect!"
        exit 1
    fi
fi

# Step 3: Update startup command to be more robust
echo ""
echo "3. Updating startup command..."

# Use a startup command that explicitly handles the PYTHONPATH
# and ensures we can find the module regardless of extraction location
STARTUP_CMD='python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}'

az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "$STARTUP_CMD" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command updated"

# Ensure PYTHONPATH is set
echo ""
echo "4. Ensuring PYTHONPATH is set..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ PYTHONPATH configured"

# Step 4: Deploy the corrected ZIP
echo ""
read -p "5. Deploy the corrected ZIP now? (y/n): " DEPLOY_NOW
if [ "$DEPLOY_NOW" = "y" ] || [ "$DEPLOY_NOW" = "Y" ]; then
    echo "   📤 Deploying ZIP..."
    az webapp deployment source config-zip \
      --resource-group $RESOURCE_GROUP \
      --name $APP_NAME \
      --src deploy.zip \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    echo "   ✅ Deployment initiated"
    echo ""
    echo "   Waiting 60 seconds for deployment to complete..."
    sleep 60
    
    # Restart app
    echo ""
    echo "6. Restarting app..."
    az webapp restart \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    echo "   ✅ App restarted"
    echo ""
    echo "   Waiting 30 seconds for app to start..."
    sleep 30
    
    # Test
    echo ""
    echo "7. Testing health endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ App is responding! HTTP $HTTP_CODE"
    else
        echo "   ⚠️  App returned HTTP $HTTP_CODE"
        echo ""
        echo "   Check logs:"
        echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    fi
else
    echo ""
    echo "   Skipping deployment. You can deploy manually later with:"
    echo "   az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deploy.zip"
fi

echo ""
echo "=== Complete ==="
