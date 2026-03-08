#!/bin/bash
# Retry deployment after checking app status

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Retrying Deployment ==="
echo ""

echo "1. Checking app status..."
APP_STATE=$(az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state -o tsv 2>/dev/null || echo "unknown")

echo "   App State: $APP_STATE"
echo ""

if [ "$APP_STATE" != "Running" ]; then
    echo "2. Starting app..."
    az webapp start \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo "   ✅ App started"
    echo ""
    echo "   Waiting 10 seconds for app to be ready..."
    sleep 10
else
    echo "2. App is already running"
    echo ""
fi

echo "3. Retrying deployment..."
cd "$SCRIPT_DIR/apps/api"

# Use the newer az webapp deploy command instead of config-zip
if az webapp deploy \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src-path deploy.zip \
  --type zip \
  --async true \
  --timeout 600 \
  2>&1 | grep -v "NotOpenSSLWarning"; then
    echo ""
    echo "   ✅ Deployment submitted"
    echo ""
    echo "   Deployment is running in the background."
    echo "   This may take 5-10 minutes."
    echo ""
    echo "   Check deployment status:"
    echo "   az webapp deployment list --name $APP_NAME --resource-group $RESOURCE_GROUP --query '[0].{Status:status,Time:active_time}' -o table"
    echo ""
    echo "   Or check logs:"
    echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
else
    echo ""
    echo "   ⚠️  New deployment method failed, trying legacy method..."
    echo ""
    
    # Fallback to legacy method
    az webapp deployment source config-zip \
      --resource-group $RESOURCE_GROUP \
      --name $APP_NAME \
      --src deploy.zip \
      2>&1 | grep -v "NotOpenSSLWarning" | head -20 || true
    
    echo ""
    echo "   ✅ Deployment command sent"
fi

echo ""
echo "=== Deployment Initiated ==="
echo ""
echo "Wait 2-3 minutes, then check status:"
echo "  curl https://$APP_NAME.azurewebsites.net/health"
echo ""
echo "Or check logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
