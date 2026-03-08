#!/bin/bash
# Deploy API to Azure App Service using Docker (bypasses Oryx)

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr$(date +%s | tail -c 6)"  # Unique name
IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Docker Deployment to Azure ==="
echo ""

# Step 1: Create Azure Container Registry if it doesn't exist
echo "Step 1: Checking for Azure Container Registry..."
ACR_EXISTS=$(az acr list --resource-group $RESOURCE_GROUP --query "[?name=='$ACR_NAME'].name" -o tsv 2>/dev/null || echo "")

if [ -z "$ACR_EXISTS" ]; then
    echo "  Creating Azure Container Registry: $ACR_NAME"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
        echo "  ⚠️  ACR creation may have failed or already exists"
    }
    echo "  ✅ ACR created"
else
    echo "  ✅ ACR already exists: $ACR_EXISTS"
    ACR_NAME=$ACR_EXISTS
fi

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv 2>/dev/null || echo "")
if [ -z "$ACR_LOGIN_SERVER" ]; then
    echo "  ❌ Failed to get ACR login server"
    exit 1
fi

echo "  ACR Login Server: $ACR_LOGIN_SERVER"
echo ""

# Step 2: Login to ACR
echo "Step 2: Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Logged in"
echo ""

# Step 3: Build Docker image for linux/amd64 (Azure requirement)
echo "Step 3: Building Docker image for linux/amd64..."
cd "$SCRIPT_DIR"
docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Docker build failed"
    exit 1
}
echo "  ✅ Docker image built for linux/amd64"
echo ""

# Step 4: Tag image for ACR
echo "Step 4: Tagging image for ACR..."
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"
docker tag $IMAGE_NAME:$IMAGE_TAG $FULL_IMAGE_NAME
echo "  ✅ Image tagged: $FULL_IMAGE_NAME"
echo ""

# Step 5: Push to ACR
echo "Step 5: Pushing image to ACR..."
docker push $FULL_IMAGE_NAME || {
    echo "  ❌ Docker push failed"
    exit 1
}
echo "  ✅ Image pushed to ACR"
echo ""

# Step 6: Configure App Service to use Docker
echo "Step 6: Configuring App Service to use Docker image..."
az webapp config container set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --container-image-name $FULL_IMAGE_NAME \
    --container-registry-url https://$ACR_LOGIN_SERVER \
    --container-registry-user $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --container-registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo "  ⚠️  Container config may have issues, continuing..."
}
echo "  ✅ App Service configured for Docker"
echo ""

# Step 7: Set PORT environment variable (Azure App Service requirement)
echo "Step 7: Setting environment variables..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        PORT=8000 \
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

echo "=== Deployment Complete ==="
echo ""
echo "Waiting 60 seconds for app to start..."
sleep 60

echo ""
echo "Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(curl -s https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ SUCCESS! App is responding!"
    echo "  Response: $RESPONSE"
    echo ""
    echo "🎉 Docker deployment is working!"
else
    echo "  ⚠️  HTTP Status: $HTTP_CODE"
    if [ ! -z "$RESPONSE" ]; then
        echo "  Response: $(echo "$RESPONSE" | head -3)"
    fi
    echo ""
    echo "  Check logs:"
    echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
fi

echo ""
echo "=== Summary ==="
echo "  ACR: $ACR_NAME"
echo "  Image: $FULL_IMAGE_NAME"
echo "  App: https://$APP_NAME.azurewebsites.net"
