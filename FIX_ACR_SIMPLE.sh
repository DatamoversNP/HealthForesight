#!/bin/bash
# Simplified ACR fix - no complex parsing, just direct commands

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"  # Set this manually if different

echo "=== SIMPLIFIED ACR IMAGE PULL FIX ==="
echo "Using ACR: $ACR_NAME"
echo ""

# Enable admin access
echo "Step 1: Enabling ACR admin access..."
az acr update --name "$ACR_NAME" --admin-enabled true >/dev/null 2>&1
echo "  ✅ Done"
echo ""

# Get credentials - suppress all output except the values
echo "Step 2: Getting ACR credentials..."
ACR_CREDS=$(az acr credential show --name "$ACR_NAME" -o json 2>/dev/null)
ACR_USER=$(echo "$ACR_CREDS" | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])" 2>/dev/null)
ACR_PASS=$(echo "$ACR_CREDS" | python3 -c "import sys, json; print(json.load(sys.stdin)['passwords'][0]['value'])" 2>/dev/null)

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ]; then
    echo "  ⚠️  Python method failed, trying direct..."
    ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv 2>/dev/null | head -1)
    ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv 2>/dev/null | head -1)
fi

if [ -z "$ACR_USER" ] || [ -z "$ACR_PASS" ] || [ "$ACR_USER" = "null" ] || [ "$ACR_PASS" = "null" ]; then
    echo "  ❌ Failed to get credentials"
    echo "  Run manually: az acr credential show --name $ACR_NAME"
    exit 1
fi

echo "  ✅ Got credentials"
echo ""

# Set container config
echo "Step 3: Setting container configuration..."
IMAGE_TAG="${ACR_NAME}.azurecr.io/uepi-api:latest"
az webapp config container set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --container-image-name "$IMAGE_TAG" \
  --container-registry-url "https://${ACR_NAME}.azurecr.io" \
  --container-registry-user "$ACR_USER" \
  --container-registry-password "$ACR_PASS" \
  >/dev/null 2>&1

echo "  ✅ Done"
echo ""

# Set app settings
echo "Step 4: Setting app settings..."
az webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    DOCKER_REGISTRY_SERVER_URL="https://${ACR_NAME}.azurecr.io" \
    DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USER" \
    DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
  >/dev/null 2>&1

echo "  ✅ Done"
echo ""

# Restart
echo "Step 5: Restarting app..."
az webapp restart --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for container to start..."
count=90
while [ $count -gt 0 ]; do
    printf "\r  ⏳ %d seconds remaining..." "$count"
    sleep 1
    count=$((count - 1))
done
echo ""
echo "  ✅ Wait complete"
echo ""

# Test
echo "Step 6: Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${APP_NAME}.azurewebsites.net/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! API is working (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL! 🎉"
    echo "API: https://${APP_NAME}.azurewebsites.net"
elif [ "$HTTP_CODE" = "503" ]; then
    echo "  ⚠️  Still HTTP 503 - container may still be starting"
    echo ""
    echo "Check logs:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP | grep -E 'ImagePullFailure|Container start|STARTUP'"
else
    echo "  ⚠️  HTTP $HTTP_CODE"
    echo ""
    echo "Check logs for errors:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Complete ==="
