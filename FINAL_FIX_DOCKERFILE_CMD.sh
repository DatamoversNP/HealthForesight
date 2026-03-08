#!/bin/bash
# Final fix: Rebuild Docker image with corrected CMD that Azure will actually use

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"

echo "=== FINAL FIX: Rebuilding with Correct CMD ==="
echo ""
echo "Problem: Azure App Service may not properly execute CMD in Dockerfile"
echo "Solution: Use a CMD format that Azure definitely supports"
echo ""

echo "Step 1: Rebuilding Docker image with fixed CMD..."
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

az acr login --name $ACR_NAME 2>&1 | grep -v "NotOpenSSLWarning" || true

docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Build failed"
    exit 1
}

echo "  ✅ Image built"
echo ""

echo "Step 2: Tagging and pushing..."
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$FULL_IMAGE_NAME"
docker push "$FULL_IMAGE_NAME" || {
    echo "  ❌ Push failed"
    exit 1
}
echo "  ✅ Image pushed"
echo ""

echo "Step 3: Getting ACR credentials..."
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv 2>&1 | grep -v "NotOpenSSLWarning" | head -1)

echo "Step 4: Updating container configuration with new image..."
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-image-name "$FULL_IMAGE_NAME" \
  --container-registry-url "https://${ACR_NAME}.azurecr.io" \
  --container-registry-user "$ACR_USER" \
  --container-registry-password "$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ Container configuration updated"
echo ""

echo "Step 5: Ensuring ACR password is set..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASS" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "  ✅ Password verified"
echo ""

echo "Step 6: Restarting app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for container to start..."
sleep 90

echo ""
echo "Step 7: Checking logs for [STARTUP] messages..."
echo "   (This will show if container is actually starting)"
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -E "STARTUP|Container|Error|Failed" | head -20 || echo "No logs yet"
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
    echo "Check detailed logs:"
    echo "  ./get_real_container_logs.sh"
    echo ""
    echo "Or manually check:"
    echo "  https://${APP_NAME}.scm.azurewebsites.net → LogFiles → docker.log"
fi
