#!/bin/bash
# Deploy with the fixed startup.sh that includes extracted directory in PYTHONPATH

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Deploying with Fixed startup.sh ==="
echo ""

cd "$SCRIPT_DIR/apps/api"

echo "1. Verifying startup.sh is updated..."
if [ -f "startup.sh" ]; then
    echo "   ✅ startup.sh exists"
    echo "   First few lines:"
    head -5 startup.sh
else
    echo "   ❌ startup.sh not found!"
    exit 1
fi
echo ""

echo "2. Creating deployment ZIP with fixed startup.sh..."
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

echo "   ✅ ZIP created"
echo ""

echo "3. Verifying startup.sh is in ZIP..."
if zipinfo deploy.zip | grep -q "startup.sh"; then
    echo "   ✅ startup.sh is in ZIP"
else
    echo "   ❌ startup.sh NOT in ZIP!"
    exit 1
fi
echo ""

echo "4. Setting startup command to use startup.sh..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "startup.sh" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ Startup command set to use startup.sh"
echo ""

echo "5. Deploying ZIP..."
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src deploy.zip \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" | grep -v "WARNING" || true

echo "   ✅ Deployment initiated"
echo ""

echo "6. Waiting 90 seconds for deployment and build..."
sleep 90

echo ""
echo "7. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App restarted"
echo ""
echo "8. Waiting 60 seconds for app to start..."
sleep 60

echo ""
echo "9. Testing health endpoint..."
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
    echo "   Check logs for [STARTUP] messages:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
