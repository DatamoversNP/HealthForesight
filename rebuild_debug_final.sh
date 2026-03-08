#!/bin/bash
# Rebuild Docker image with debug output and redeploy - uses known ACR

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
ACR_NAME="healthforesightacr12666"  # Known from earlier

echo "=== Rebuilding with Debug Output ==="
echo ""

echo "Step 1: ACR: $ACR_NAME"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
echo "  ACR Login Server: $ACR_LOGIN_SERVER"
echo ""

echo "Step 2: Logging in to ACR..."
az acr login --name $ACR_NAME --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Logged in"
echo ""

echo "Step 3: Rebuilding Docker image..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Docker build failed"
    exit 1
}
echo "  ✅ Image built"
echo ""

echo "Step 4: Tagging and pushing to ACR..."
echo "  Tagging: $IMAGE_NAME:$IMAGE_TAG -> $FULL_IMAGE_NAME"
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$FULL_IMAGE_NAME" || {
    echo "  ❌ Tag failed"
    exit 1
}
echo "  Pushing..."
docker push "$FULL_IMAGE_NAME" || {
    echo "  ❌ Push failed"
    exit 1
}
echo "  ✅ Image pushed"
echo ""

echo "Step 5: Restarting app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for container to start..."
sleep 90

echo ""
echo "Check logs for [STARTUP] messages:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP | grep -A 10 '[STARTUP]'"
echo ""

echo "Or get full logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""

echo "Test endpoint:"
echo "  curl https://$APP_NAME.azurewebsites.net/health"
echo ""
