#!/bin/bash
# Fix Azure Docker container configuration

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"

echo "=== Fixing Azure Docker Configuration ==="
echo ""

echo "1. Checking current container configuration..."
CONFIG=$(az webapp config show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "linuxFxVersion" -o tsv 2>/dev/null || echo "")
echo "   Current: $CONFIG"
echo ""

echo "2. Ensuring Docker container logging is enabled..."
az webapp log config \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-container-logging filesystem \
    --level verbose \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "   ✅ Container logging enabled"
echo ""

echo "3. Checking container registry credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>/dev/null || echo "")
ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>/dev/null || echo "")

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ]; then
    echo "   ⚠️  Could not get ACR credentials"
else
    echo "   ✅ ACR credentials available"
fi

echo ""
echo "4. Re-configuring container settings..."
FULL_IMAGE="healthforesightacr12666.azurecr.io/uepi-api:latest"

az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --container-image-name "$FULL_IMAGE" \
    --container-registry-url "https://healthforesightacr12666.azurecr.io" \
    --container-registry-user "$ACR_USER" \
    --container-registry-password "$ACR_PASS" \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "   ⚠️  Container config may have issues"
}
echo "   ✅ Container configured"
echo ""

echo "5. Ensuring PORT environment variable is set..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        PORT=8000 \
        PYTHONPATH="/app/src:/app/packages/common/src" \
        WEBSITES_PORT=8000 \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "   ✅ Environment variables set"
echo ""

echo "6. Restarting app..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "   ✅ App restarted"
echo ""

echo "7. Waiting 60 seconds for container to start..."
sleep 60

echo ""
echo "8. Checking logs..."
az webapp log tail \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    2>&1 | grep -v "NotOpenSSLWarning" | head -50

echo ""
echo "=== Complete ==="
