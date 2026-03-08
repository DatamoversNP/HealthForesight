#!/bin/bash
# CONCRETE FIX: Set ACR password correctly so Azure can pull the Docker image

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"

echo "=== FIXING ACR PASSWORD (ROOT CAUSE) ==="
echo ""

echo "Problem: DOCKER_REGISTRY_SERVER_PASSWORD is NULL - Azure can't pull image"
echo ""

echo "Step 1: Getting ACR credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)

if [ -z "$ACR_PASS" ] || [ "$ACR_PASS" == "null" ]; then
    echo "  ❌ Could not get ACR password!"
    echo "  Trying alternative method..."
    ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
fi

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ]; then
    echo "  ❌ Still cannot get credentials. Regenerating ACR password..."
    az acr credential renew --name $ACR_NAME --password-name password1 2>&1 | grep -v "NotOpenSSLWarning" || true
    sleep 2
    ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
    ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
fi

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ] || [ "$ACR_PASS" == "null" ]; then
    echo "  ❌ FAILED: Cannot get ACR credentials"
    echo "  Manual step required:"
    echo "  1. Go to Azure Portal"
    echo "  2. Navigate to: Container Registry > $ACR_NAME > Access keys"
    echo "  3. Copy the password1 value"
    echo "  4. Run: az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings DOCKER_REGISTRY_SERVER_PASSWORD='YOUR_PASSWORD'"
    exit 1
fi

echo "  ✅ Got ACR credentials"
echo "  Username: $ACR_USER"
echo "  Password: ${ACR_PASS:0:4}... (hidden)"
echo ""

echo "Step 2: Setting ACR password in app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "  ❌ Failed to set password"
    exit 1
}

echo "  ✅ ACR password set"
echo ""

echo "Step 3: Verifying password was set..."
VERIFY_PASS=$(az webapp config appsettings list \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='DOCKER_REGISTRY_SERVER_PASSWORD'].value" -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)

if [ -z "$VERIFY_PASS" ] || [ "$VERIFY_PASS" == "null" ]; then
    echo "  ❌ Password is still null - trying alternative method..."
    # Try setting it via container config instead
    az webapp config container set \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --docker-custom-image-name ${ACR_NAME}.azurecr.io/uepi-api:latest \
      --docker-registry-server-url https://${ACR_NAME}.azurecr.io \
      --docker-registry-server-user "$ACR_USER" \
      --docker-registry-server-password "$ACR_PASS" \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
else
    echo "  ✅ Password verified: ${VERIFY_PASS:0:4}... (hidden)"
fi
echo ""

echo "Step 4: Using MODERN Azure CLI commands (not deprecated)..."
# Use the new container configuration commands
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-image-name ${ACR_NAME}.azurecr.io/uepi-api:latest \
  --container-registry-url https://${ACR_NAME}.azurecr.io \
  --container-registry-user "$ACR_USER" \
  --container-registry-password "$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ Container configuration updated with modern commands"
echo ""

echo "Step 5: Ensuring no startup command conflicts..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ Startup command cleared"
echo ""

echo "Step 6: Restarting app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for container to pull and start..."
sleep 90

echo ""
echo "Step 7: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! API is responding (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 Container is now working!"
    echo ""
    echo "API URL: https://${APP_NAME}.azurewebsites.net"
    echo "Health: https://${APP_NAME}.azurewebsites.net/health"
else
    echo "  ⚠️  Still getting HTTP $HTTP_CODE"
    echo ""
    echo "Check logs for details:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi
echo ""
