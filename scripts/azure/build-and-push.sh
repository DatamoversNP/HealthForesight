#!/bin/bash
# Build and push Docker images to Azure Container Registry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}UEPI Docker Image Build and Push${NC}"
echo "======================================"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found. Please install it.${NC}" >&2; exit 1; }
command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI not found. Please install it.${NC}" >&2; exit 1; }

# Check Azure login
az account show >/dev/null 2>&1 || { 
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
}

# Get ACR name from environment or prompt
if [ -z "$ACR_NAME" ]; then
    read -p "Enter Azure Container Registry name [uepiacr]: " ACR_NAME
    ACR_NAME=${ACR_NAME:-uepiacr}
fi

# Get resource group (optional, for ACR lookup)
if [ -z "$RESOURCE_GROUP" ]; then
    read -p "Enter resource group (optional, press Enter to skip): " RESOURCE_GROUP
fi

# Login to ACR
echo -e "${YELLOW}Logging in to Azure Container Registry...${NC}"
az acr login --name "${ACR_NAME}"

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "${ACR_NAME}" --query loginServer -o tsv)
echo -e "${GREEN}Using ACR: ${ACR_LOGIN_SERVER}${NC}"

# Build context
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# Image tags
VERSION=${VERSION:-latest}
API_IMAGE="${ACR_LOGIN_SERVER}/uepi-api:${VERSION}"
WORKER_IMAGE="${ACR_LOGIN_SERVER}/uepi-worker:${VERSION}"
WEB_IMAGE="${ACR_LOGIN_SERVER}/uepi-web:${VERSION}"

echo -e "${GREEN}Building images...${NC}"

# Build API image (for linux/amd64 platform for Azure)
echo -e "${YELLOW}Building API image...${NC}"
docker buildx build --platform linux/amd64 -t "${API_IMAGE}" \
    -f apps/api/Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --load \
    .

# Build Worker image (for linux/amd64 platform for Azure)
echo -e "${YELLOW}Building Worker image...${NC}"
docker buildx build --platform linux/amd64 -t "${WORKER_IMAGE}" \
    -f apps/worker/Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --load \
    .

# Build Web image (for linux/amd64 platform for Azure)
echo -e "${YELLOW}Building Web image...${NC}"
docker buildx build --platform linux/amd64 -t "${WEB_IMAGE}" \
    -f apps/web/Dockerfile \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --load \
    .

# Push images
echo -e "${GREEN}Pushing images to ACR...${NC}"
docker push "${API_IMAGE}"
docker push "${WORKER_IMAGE}"
docker push "${WEB_IMAGE}"

echo -e "${GREEN}✅ All images built and pushed successfully!${NC}"
echo ""
echo "Images:"
echo "  - ${API_IMAGE}"
echo "  - ${WORKER_IMAGE}"
echo "  - ${WEB_IMAGE}"
echo ""
echo "Next: Run deployment script to deploy to AKS"

