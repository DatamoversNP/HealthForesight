#!/bin/bash
# Rebuild Docker image with debug output and redeploy

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Rebuilding with Debug Output ==="
echo ""

# Step 1: Find existing ACR
echo "Step 1: Finding Azure Container Registry..."
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -z "$ACR_NAME" ]; then
    # Try to find any ACR in subscription
    ACR_NAME=$(az acr list --query "[?contains(name, 'healthforesight')].name" -o tsv 2>/dev/null | head -1 || echo "")
fi
if [ -z "$ACR_NAME" ]; then
    echo "  ❌ No ACR found."
    echo "  Please provide ACR name, or run deploy_with_docker.sh first."
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

# Step 3: Build for linux/amd64 with debug
echo "Step 3: Rebuilding Docker image with debug output..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

# Build with --platform linux/amd64
docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Docker build failed"
    exit 1
}
echo "  ✅ Image built for linux/amd64 with debug output"
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

# Step 6: Configure App Service
echo "Step 6: Configuring App Service..."
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

# Step 7: Set environment variables
echo "Step 7: Setting environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        PORT=8000 \
        WEBSITES_PORT=8000 \
        PYTHONPATH="/app/src:/app/packages/common/src" \
        STORAGE_PATH="/home/data" \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Environment variables set"
echo ""

# Step 8: Enable logging
echo "Step 8: Enabling detailed logging..."
az webapp log config \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --application-logging filesystem \
    --level verbose \
    --docker-container-logging filesystem \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Logging enabled"
echo ""

# Step 9: Restart app
echo "Step 9: Restarting app..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "=== Deployment Complete ==="
echo ""
echo "Waiting 90 seconds for container to start..."
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
    echo "  Check logs for [STARTUP] messages:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP | grep -A 20 '[STARTUP]'"
    echo ""
    echo "  Or get full container logs:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Summary ==="
echo "  ACR: $ACR_NAME"
echo "  Image: $FULL_IMAGE_NAME"
echo "  Platform: linux/amd64"
echo "  Storage Path: /home/data"
echo "  Debug: Enabled (look for [STARTUP] in logs)"
echo "  App: https://$APP_NAME.azurewebsites.net"
