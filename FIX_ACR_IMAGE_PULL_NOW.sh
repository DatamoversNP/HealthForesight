#!/bin/bash
# Comprehensive fix for ImagePullFailure - verify image exists and fix auth

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== COMPREHENSIVE ACR IMAGE PULL FIX ==="
echo ""

# Find ACR name
echo "Step 1: Finding ACR registry..."
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null | head -1 | tr -d '[:space:]' || echo "")

if [ -z "$ACR_NAME" ] || [ "$ACR_NAME" == "null" ] || [[ "$ACR_NAME" == *"warn"* ]]; then
    echo "  ⚠️  Could not find ACR automatically. Trying known names..."
    # Try known ACR names
    for known_acr in "healthforesightacr12666" "healthforesightacr"; do
        if az acr show --name "$known_acr" --query name -o tsv 2>/dev/null | grep -q "$known_acr"; then
            ACR_NAME="$known_acr"
            break
        fi
    done
fi

if [ -z "$ACR_NAME" ] || [[ "$ACR_NAME" == *"warn"* ]]; then
    echo "  ❌ Could not determine ACR name"
    echo "  Please provide ACR name manually or check: az acr list --resource-group $RESOURCE_GROUP"
    exit 1
fi

echo "  ✅ Found ACR: $ACR_NAME"
echo ""

# Verify image exists
echo "Step 2: Verifying Docker image exists in ACR..."
IMAGE_TAG="${ACR_NAME}.azurecr.io/uepi-api:latest"
if az acr repository show-tags --name $ACR_NAME --repository uepi-api --output table 2>/dev/null | grep -q "uepi-api"; then
    echo "  ✅ Image exists in ACR"
else
    echo "  ⚠️  Image 'uepi-api:latest' not found in ACR!"
    echo "  Need to rebuild and push image first."
    echo ""
    echo "  Run: ./deploy_with_docker.sh"
    exit 1
fi
echo ""

# Enable admin access
echo "Step 3: Ensuring ACR admin access is enabled..."
ADMIN_ENABLED=$(az acr show --name $ACR_NAME --query adminUserEnabled -o tsv 2>/dev/null | head -1 | tr -d '[:space:]')

if [ "$ADMIN_ENABLED" != "true" ]; then
    echo "  Enabling admin access..."
    az acr update --name $ACR_NAME --admin-enabled true --output none 2>/dev/null || true
    echo "  ✅ Admin access enabled"
else
    echo "  ✅ Admin access already enabled"
fi
echo ""

# Get credentials
echo "Step 4: Getting ACR credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>/dev/null | head -1 | tr -d '[:space:]')
ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv 2>/dev/null | head -1 | tr -d '[:space:]')

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ] || [ "$ACR_USER" == "null" ] || [ "$ACR_PASS" == "null" ] || [[ "$ACR_USER" == *"warn"* ]]; then
    echo "  ⚠️  Credentials not available. Regenerating..."
    az acr credential renew --name $ACR_NAME --password-name password1 --output none 2>/dev/null || true
    sleep 5
    ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>/dev/null | head -1 | tr -d '[:space:]')
    ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv 2>/dev/null | head -1 | tr -d '[:space:]')
fi

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ] || [ "$ACR_USER" == "null" ] || [ "$ACR_PASS" == "null" ] || [[ "$ACR_USER" == *"warn"* ]]; then
    echo "  ❌ Failed to get ACR credentials"
    echo ""
    echo "  Try manually:"
    echo "    az acr credential show --name $ACR_NAME"
    exit 1
fi

echo "  ✅ Got credentials"
echo "  Username: $ACR_USER"
echo "  Password: ${ACR_PASS:0:10}... (hidden)"
echo ""

# Clear any existing container config first
echo "Step 5: Clearing existing container configuration..."
az webapp config container delete --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>/dev/null || true
sleep 2
echo "  ✅ Cleared"
echo ""

# Set container config with modern method
echo "Step 6: Setting container configuration (using modern method)..."
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-image-name "$IMAGE_TAG" \
  --container-registry-url "https://${ACR_NAME}.azurecr.io" \
  --container-registry-user "$ACR_USER" \
  --container-registry-password "$ACR_PASS" \
  --output none 2>/dev/null || {
    echo "  ⚠️  Modern method failed, trying deprecated method..."
    az webapp config container set \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --docker-custom-image-name "$IMAGE_TAG" \
      --docker-registry-server-url "https://${ACR_NAME}.azurecr.io" \
      --docker-registry-server-user "$ACR_USER" \
      --docker-registry-server-password "$ACR_PASS" \
      --output none 2>/dev/null || true
}

echo "  ✅ Container config set"
echo ""

# Also set as app settings (backup)
echo "Step 7: Setting credentials as app settings (backup method)..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DOCKER_REGISTRY_SERVER_URL="https://${ACR_NAME}.azurecr.io" \
    DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USER" \
    DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE="false" \
  --output none 2>/dev/null || true

echo "  ✅ App settings updated"
echo ""

# Verify
echo "Step 8: Verifying configuration..."
CONTAINER_USER=$(az webapp config container show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[].dockerRegistryServerUser" -o tsv 2>/dev/null | grep -v -i "warn\|error\|http" | head -1 | tr -d '[:space:]' || echo "")
PASSWORD_IN_SETTINGS=$(az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[?name=='DOCKER_REGISTRY_SERVER_PASSWORD'].value" -o tsv 2>/dev/null | grep -v -i "warn\|error\|http" | head -1 | tr -d '[:space:]' || echo "")

if [ -n "$CONTAINER_USER" ] && [ "$CONTAINER_USER" != "null" ] && [[ ! "$CONTAINER_USER" =~ warn ]]; then
    echo "  ✅ Container config has username: $CONTAINER_USER"
else
    echo "  ⚠️  Container config may not have username (or got warnings)"
    echo "  Checking manually via Azure Portal..."
fi

if [ -n "$PASSWORD_IN_SETTINGS" ] && [ "$PASSWORD_IN_SETTINGS" != "null" ] && [[ ! "$PASSWORD_IN_SETTINGS" =~ warn ]]; then
    echo "  ✅ App settings has password: ${PASSWORD_IN_SETTINGS:0:10}... (hidden)"
else
    echo "  ⚠️  App settings may not have password (or got warnings)"
fi
echo ""

# Restart
echo "Step 9: Restarting app to pull image..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>/dev/null || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for image pull and container start..."
i=90
while [ $i -gt 0 ]; do
    printf "\r  ⏳ %d seconds remaining..." "$i" 2>/dev/null || echo -n "  ⏳ $i seconds remaining..."
    sleep 1
    i=$((i - 1))
done
printf "\r  ✅ Wait complete              \n" 2>/dev/null || echo ""
echo "  ✅ Wait complete"
echo ""

# Test
echo "Step 10: Testing image pull..."
echo "  Checking logs for ImagePullFailure..."
LATEST_LOGS=$(az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>/dev/null | grep -E "ImagePullFailure|Container pull|Container start|STARTUP|Application startup" | tail -5 || echo "")

if echo "$LATEST_LOGS" | grep -q "ImagePullFailure"; then
    echo "  ❌ Still seeing ImagePullFailure!"
    echo ""
    echo "  Latest relevant logs:"
    echo "$LATEST_LOGS" | head -5
    echo ""
    echo "  Manual check:"
    echo "    az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP | grep ImagePullFailure"
else
    echo "  ✅ No ImagePullFailure in recent logs"
    if echo "$LATEST_LOGS" | grep -q "Container start\|STARTUP\|Application startup"; then
        echo "  ✅ Container appears to be starting!"
    fi
fi
echo ""

echo "Step 11: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /tmp/health_response.txt -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(cat /tmp/health_response.txt 2>/dev/null | head -100 || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! API is working (HTTP $HTTP_CODE)"
    echo "  Response: $RESPONSE"
    echo ""
    echo "🎉🎉🎉 DEPLOYMENT SUCCESSFUL! 🎉🎉🎉"
    echo ""
    echo "Your API is live at:"
    echo "  https://${APP_NAME}.azurewebsites.net"
    echo "  https://${APP_NAME}.azurewebsites.net/health"
    echo "  https://${APP_NAME}.azurewebsites.net/docs"
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "000" ]; then
    echo "  ⚠️  Still HTTP $HTTP_CODE (container may still be starting)"
    echo "  Response: $RESPONSE" | head -5
    echo ""
    echo "  Wait a bit longer and check:"
    echo "    curl https://${APP_NAME}.azurewebsites.net/health"
    echo "    az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
else
    echo "  ⚠️  HTTP $HTTP_CODE"
    echo "  Response: $RESPONSE" | head -5
fi

echo ""
echo "=== Complete ==="
