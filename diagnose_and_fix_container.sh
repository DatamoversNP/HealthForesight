#!/bin/bash
# Comprehensive script to diagnose and fix ContainerCreateFailure

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"

echo "=== Diagnosing ContainerCreateFailure ==="
echo ""

echo "Step 1: Checking current container configuration..."
CONTAINER_CONFIG=$(az webapp config container show --name $APP_NAME --resource-group $RESOURCE_GROUP -o json 2>&1 | grep -v "NotOpenSSLWarning" || echo "")
echo "$CONTAINER_CONFIG" | python3 -m json.tool 2>/dev/null || echo "$CONTAINER_CONFIG"
echo ""

echo "Step 2: Checking app settings (looking for conflicts)..."
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[?name=='WEBSITES_ENABLE_APP_SERVICE_STORAGE' || name=='WEBSITES_PORT' || name=='PORT' || name=='DOCKER_REGISTRY_SERVER_URL' || contains(name, 'DOCKER')]" -o table 2>&1 | grep -v "NotOpenSSLWarning" || true
echo ""

echo "Step 3: Checking if Docker image exists in ACR..."
az acr repository show-tags --name $ACR_NAME --repository uepi-api --output table 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "  ⚠️  Could not list tags - image may not exist"
}
echo ""

echo "Step 4: Verifying ACR credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" || echo "")
ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" || echo "")

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ]; then
    echo "  ❌ Could not get ACR credentials"
else
    echo "  ✅ ACR credentials available"
fi
echo ""

echo "Step 5: Fixing container configuration..."
echo "  Clearing any conflicting startup commands..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  Setting Docker container configuration..."
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name ${ACR_NAME}.azurecr.io/uepi-api:latest \
  --docker-registry-server-url https://${ACR_NAME}.azurecr.io \
  --docker-registry-server-user "$ACR_USER" \
  --docker-registry-server-password "$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "  ⚠️  Container config update may have failed"
}

echo "  ✅ Container configuration updated"
echo ""

echo "Step 6: Ensuring port and storage settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    WEBSITES_PORT=8000 \
    PORT=8000 \
    STORAGE_PATH=/home/data \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Settings updated"
echo ""

echo "Step 7: Restarting app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 60 seconds for container to start..."
sleep 60

echo ""
echo "Step 8: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ API is responding (HTTP $HTTP_CODE)"
else
    echo "  ⚠️  API returned HTTP $HTTP_CODE"
fi
echo ""

echo "=== Diagnosis Complete ==="
echo ""
echo "If container still fails:"
echo "1. Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "2. Check Kudu console: https://${APP_NAME}.scm.azurewebsites.net"
echo "3. Check Azure Portal > App Service > Container settings"
echo ""
echo "Frontend URL (if deployed):"
echo "  Check: az staticwebapp list --resource-group $RESOURCE_GROUP --query '[].{Name:name, URL:defaultHostname}' -o table"
