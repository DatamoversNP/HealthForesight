#!/bin/bash
# Fix Docker container creation failure in Azure App Service

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing Container Creation Issue ==="
echo ""

# Find existing ACR in the resource group
echo "Finding Azure Container Registry..."

# Known ACR name from previous deployments
KNOWN_ACR="healthforesightacr12666"

# Try to get ACR name from Azure (suppress warnings to stderr)
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null | head -1 | tr -d '[:space:]' || echo "")

# Validate and use known ACR if auto-detection failed
if [ -z "$ACR_NAME" ] || [ "$ACR_NAME" == "null" ] || [[ ! "$ACR_NAME" =~ ^[a-z0-9]+$ ]]; then
    echo "  ⚠️  Auto-detection failed, using known ACR: $KNOWN_ACR"
    ACR_NAME=$KNOWN_ACR
else
    echo "  ✅ Found ACR: $ACR_NAME"
fi

# Allow override via environment variable
if [ -n "$ACR_NAME_OVERRIDE" ]; then
    ACR_NAME="$ACR_NAME_OVERRIDE"
    echo "  ℹ️  Using ACR from ACR_NAME_OVERRIDE: $ACR_NAME"
fi

# Final validation
if [[ ! "$ACR_NAME" =~ ^[a-z0-9]+$ ]]; then
    echo "  ❌ Invalid ACR name: '$ACR_NAME'"
    echo "  Please set ACR_NAME_OVERRIDE environment variable"
    exit 1
fi

echo "  Using ACR: $ACR_NAME"

echo ""

echo "Step 1: Ensuring startup command is NOT set (use Dockerfile CMD)..."
# Clear any conflicting startup command - let Dockerfile CMD handle it
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Startup command cleared"
echo ""

echo "Step 2: Ensuring WEBSITES_PORT is set..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings WEBSITES_PORT=8000 \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Port configured"
echo ""

echo "Step 3: Ensuring PORT environment variable is set..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings PORT=8000 \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ PORT set"
echo ""

echo "Step 4: Rebuilding Docker image..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
IMAGE_NAME="uepi-api"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"

echo "  Logging in to ACR: $ACR_NAME..."
az acr login --name $ACR_NAME 2>&1 | grep -v "NotOpenSSLWarning" | grep -v "warnings.warn" || {
    echo "  ⚠️  ACR login may have shown warnings (continuing anyway)"
}
echo "  ✅ ACR login completed"

echo "  Building image..."
docker build --platform linux/amd64 -t $IMAGE_NAME:$IMAGE_TAG -f apps/api/Dockerfile . || {
    echo "  ❌ Build failed"
    exit 1
}

echo "  Tagging and pushing..."
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$FULL_IMAGE_NAME"
docker push "$FULL_IMAGE_NAME" || {
    echo "  ❌ Push failed"
    exit 1
}
echo "  ✅ Image rebuilt and pushed"
echo ""

echo "Step 5: Restarting app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "Waiting 90 seconds for container to start..."
sleep 90

echo ""
echo "Check logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "Test health endpoint:"
echo "  curl https://$APP_NAME.azurewebsites.net/health"
echo ""
