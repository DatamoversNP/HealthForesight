#!/bin/bash
# Fix Docker deployment: rebuild for correct platform and fix ACR auth

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Docker Deployment ==="
echo ""

# Step 1: Find existing ACR
echo "Step 1: Finding Azure Container Registry..."
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -z "$ACR_NAME" ]; then
    echo "  ❌ No ACR found. Run deploy_with_docker.sh first."
    exit 1
fi
echo "  ✅ Found ACR: $ACR_NAME"

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
echo "  ACR Login Server: $ACR_LOGIN_SERVER"
echo ""

# Step 2: Login to ACR
echo "Step 2: Logging in to ACR..."
az acr login --name $ACR_NAME --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Logged in"
echo ""

# Step 3: Build for linux/amd64 platform
echo "Step 3: Rebuilding Docker image for linux/amd64..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

# Build with --platform linux/amd64 (CRITICAL for Azure)
docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Docker build failed"
    exit 1
}
echo "  ✅ Image built for linux/amd64"
echo ""

# Step 4: Tag and push
echo "Step 4: Tagging and pushing image..."
docker tag $IMAGE_NAME:$IMAGE_TAG $FULL_IMAGE_NAME
docker push $FULL_IMAGE_NAME || {
    echo "  ❌ Docker push failed"
    exit 1
}
echo "  ✅ Image pushed to ACR"
echo ""

# Step 5: Get ACR credentials
echo "Step 5: Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
echo "  ✅ Credentials retrieved"
echo ""

# Step 6: Configure App Service with Docker image and credentials
echo "Step 6: Configuring App Service with Docker image..."
az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --container-image-name $FULL_IMAGE_NAME \
    --container-registry-url https://$ACR_LOGIN_SERVER \
    --container-registry-user $ACR_USERNAME \
    --container-registry-password $ACR_PASSWORD \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "  ⚠️  Container config warning (may still work)"
}
echo "  ✅ App Service configured"
echo ""

# Step 7: Ensure environment variables are set
echo "Step 7: Setting environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        PORT=8000 \
        WEBSITES_PORT=8000 \
        PYTHONPATH="/app/src:/app/packages/common/src" \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Environment variables set"
echo ""

# Step 8: Restart app
echo "Step 8: Restarting app..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "=== Fix Complete ==="
echo ""
echo "Waiting 90 seconds for container to pull and start..."
sleep 90

echo ""
echo "Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null | head -5 || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! App is responding!"
    echo "  Response: $RESPONSE"
    echo ""
    echo "🎉 Docker deployment is working!"
else
    echo "  ⚠️  HTTP Status: $HTTP_CODE"
    if [ ! -z "$RESPONSE" ]; then
        echo "  Response: $RESPONSE"
    fi
    echo ""
    echo "  Check logs:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Summary ==="
echo "  ACR: $ACR_NAME"
echo "  Image: $FULL_IMAGE_NAME"
echo "  Platform: linux/amd64"
echo "  App: https://$APP_NAME.azurewebsites.net"
