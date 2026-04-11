#!/usr/bin/env bash
# Deploy HealthForesight API as a Docker container to Azure App Service.
# Use this when zip deploy keeps failing with "Site failed to start within 10 mins".
# Builds the image in Azure (az acr build) – no Docker required on your machine.
# Prerequisites: Azure CLI (az login).
#
# Usage (from repo root):
#   ./scripts/azure/deploy-api-docker.sh
#
# Optional env:
#   ACR_NAME=myacr          Azure Container Registry name (default: healthforesightacr)
#   RESOURCE_GROUP=...      (default: healthforesight-rg)
#   API_APP_NAME=...        (default: healthforesight-api)
set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
ACR_NAME="${ACR_NAME:-healthforesightacr}"
IMAGE_NAME="healthforesight-api"
# Prefer a unique tag so App Service pulls a new image (``latest`` is often cached after restart).
if [[ -z "${IMAGE_TAG:-}" ]]; then
  if GIT_SHORT=$(git -C "$(dirname "$0")/../.." rev-parse --short HEAD 2>/dev/null); then
    IMAGE_TAG="$GIT_SHORT"
  else
    IMAGE_TAG="latest"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "HealthForesight API – Docker deploy"
echo "=============================================="
echo "Resource group: $RESOURCE_GROUP"
echo "Web App:       $API_APP_NAME"
echo "ACR:           $ACR_NAME"
echo "Image tag:     $IMAGE_TAG"
echo ""

# Create ACR if it doesn't exist
if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "Creating Azure Container Registry: $ACR_NAME ..."
  az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic --output none
fi

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
FULL_IMAGE="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

# Build in Azure (no local Docker needed); context is repo root, respects .dockerignore
echo "Building API image in Azure Container Registry (no local Docker required)..."
az acr build --registry "$ACR_NAME" --image "${IMAGE_NAME}:${IMAGE_TAG}" --image "${IMAGE_NAME}:latest" --file apps/api/Dockerfile .

# Enable admin user on ACR so Web App can pull (or use managed identity; admin is simpler for one-off)
echo "Ensuring ACR admin user is enabled..."
az acr update --name "$ACR_NAME" --admin-enabled true --output none 2>/dev/null || true

ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

echo "Configuring Web App to use container (tag: ${IMAGE_TAG})..."
az webapp config container set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --docker-custom-image-name "$FULL_IMAGE" \
  --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
  --docker-registry-server-user "$ACR_USER" \
  --docker-registry-server-password "$ACR_PASS" \
  --output none

# Container listens on PORT (Azure) / WEBSITES_PORT (app setting); docker-entrypoint uses PORT first, then WEBSITES_PORT, else 8080.
echo "Setting WEBSITES_PORT, PORT, PYTHONPATH (portal PYTHONPATH overrides image ENV and breaks uepi_common)..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --settings \
    WEBSITES_PORT=8080 \
    PORT=8080 \
    PYTHONPATH=/app/apps/api/src:/app/packages/common/src:/app/apps/worker/src \
  --output none

# Portal "Startup command: startup.sh" is for ZIP/Oryx; it is NOT in the Docker image → container exits → 503.
echo "Clearing App Service startup command (use image CMD only)..."
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --startup-command "" \
  --output none 2>/dev/null || true

echo "Restarting Web App..."
az webapp restart --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none

echo ""
echo "=============================================="
echo "Docker deploy complete"
echo "=============================================="
echo "API URL: https://$API_APP_NAME.azurewebsites.net"
echo "Image:   $FULL_IMAGE"
echo ""
echo "Allow 1–2 minutes for the container to start, then:"
echo "  curl -s https://$API_APP_NAME.azurewebsites.net/api/v1/ping"
echo ""
echo "Heavy claims analytics: API uses SET LOCAL up to 300s on breakdown endpoints; optional app setting"
echo "  PG_STATEMENT_TIMEOUT_MS=120000  (raises default per-connection Postgres cap from 10s if needed)"
echo ""
echo "Production (API + Redis + Celery worker + app settings):"
echo "  scripts/azure/DEPLOY_PRODUCTION_AZURE.md  and  deploy-production-stack.sh"
echo ""
echo "If still 503: Log stream should show the entrypoint line with listen port."
echo "Stack check (linuxFxVersion should start with DOCKER|):"
az webapp config show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" \
  --query "{linuxFxVersion:linuxFxVersion, appCommandLine:appCommandLine}" -o json 2>/dev/null || true
echo ""
