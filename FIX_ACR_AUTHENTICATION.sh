#!/bin/bash
# Fix ACR authentication - enable admin access and set credentials correctly

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"

echo "=== FIXING ACR AUTHENTICATION (ImagePullFailure) ==="
echo ""

echo "Step 1: Enabling ACR admin access (required for App Service)..."
az acr update --name $ACR_NAME --admin-enabled true 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Admin access enabled"
echo ""

echo "Step 2: Getting fresh ACR credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1 | tr -d '[:space:]')
ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1 | tr -d '[:space:]')

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ] || [ "$ACR_USER" == "null" ] || [ "$ACR_PASS" == "null" ]; then
    echo "  ⚠️  Could not get credentials. Regenerating..."
    az acr credential renew --name $ACR_NAME --password-name password1 2>&1 | grep -v "NotOpenSSLWarning" || true
    sleep 3
    ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1 | tr -d '[:space:]')
    ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1 | tr -d '[:space:]')
fi

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ]; then
    echo "  ❌ Failed to get ACR credentials"
    exit 1
fi

echo "  ✅ Got credentials"
echo "  Username: $ACR_USER"
echo "  Password: ${ACR_PASS:0:8}... (hidden)"
echo ""

echo "Step 3: Setting ACR credentials in App Service (modern method)..."
# Use the modern container config command
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-image-name ${ACR_NAME}.azurecr.io/uepi-api:latest \
  --container-registry-url https://${ACR_NAME}.azurecr.io \
  --container-registry-user "$ACR_USER" \
  --container-registry-password "$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ Container config updated"
echo ""

echo "Step 4: ALSO setting password in app settings (backup method)..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DOCKER_REGISTRY_SERVER_URL="https://${ACR_NAME}.azurecr.io" \
    DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USER" \
    DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ App settings updated"
echo ""

echo "Step 5: Verifying credentials are set..."
CONTAINER_CONFIG=$(az webapp config container show --name $APP_NAME --resource-group $RESOURCE_GROUP -o json 2>&1 | grep -v "NotOpenSSLWarning" || echo "")
PASSWORD_SET=$(az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[?name=='DOCKER_REGISTRY_SERVER_PASSWORD'].value" -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1 | tr -d '[:space:]')

if [ -n "$PASSWORD_SET" ] && [ "$PASSWORD_SET" != "null" ]; then
    echo "  ✅ Password is set: ${PASSWORD_SET:0:8}... (hidden)"
else
    echo "  ⚠️  Password may not be set correctly"
fi
echo ""

echo "Step 6: Restarting app to pull image with new credentials..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 60 seconds for image pull and container start..."
sleep 60

echo ""
echo "Step 7: Testing if image was pulled successfully..."
echo "  Check logs for 'ImagePullFailure' (should be gone now)"
echo ""
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -E "ImagePullFailure|Container pull|STARTUP|Application startup" | head -10 || echo "  No relevant logs yet"
echo ""

echo "Step 8: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! API is working (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 Container is now running!"
    echo "API: https://${APP_NAME}.azurewebsites.net"
else
    echo "  ⚠️  Still HTTP $HTTP_CODE"
    echo ""
    echo "Check if ImagePullFailure is gone:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP | grep ImagePullFailure"
fi
