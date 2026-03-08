#!/bin/bash
# Deploy Policy Catalog and Data Viewer updates to Azure
# This script builds new Docker images and deploys them to AKS

set -e

# Configuration
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-uepiregistry.azurecr.io}"
RESOURCE_GROUP="${RESOURCE_GROUP:-uepi-rg}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-uepi-aks}"
NAMESPACE="${NAMESPACE:-uepi-prod}"

echo "=========================================="
echo "🚀 Deploying Policy Catalog & Data Viewer Updates"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Image Tag: $IMAGE_TAG"
echo "  Image Registry: $IMAGE_REGISTRY"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  AKS Cluster: $AKS_CLUSTER_NAME"
echo "  Namespace: $NAMESPACE"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI not found"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm not found"; exit 1; }

# Check Azure login
az account show >/dev/null 2>&1 || {
    echo "Please login to Azure..."
    az login
}

# Get AKS credentials
echo "🔧 Getting AKS credentials..."
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" --overwrite-existing

# Login to ACR
echo "🔐 Logging into Azure Container Registry..."
az acr login --name "${IMAGE_REGISTRY%.azurecr.io}" || {
    echo "⚠️  Could not login to ACR. Make sure ACR name is correct."
    echo "   Expected format: <name>.azurecr.io"
    echo "   Got: $IMAGE_REGISTRY"
    exit 1
}

# Build and push API image
echo ""
echo "📦 Building API image..."
cd "$(dirname "$0")/../.."
docker build \
    --platform linux/amd64 \
    -t "${IMAGE_REGISTRY}/uepi/api:${IMAGE_TAG}" \
    -t "${IMAGE_REGISTRY}/uepi/api:latest" \
    -f apps/api/Dockerfile .

echo "📤 Pushing API image..."
docker push "${IMAGE_REGISTRY}/uepi/api:${IMAGE_TAG}"
docker push "${IMAGE_REGISTRY}/uepi/api:latest"

# Build and push Worker image
echo ""
echo "📦 Building Worker image..."
docker build \
    --platform linux/amd64 \
    -t "${IMAGE_REGISTRY}/uepi/worker:${IMAGE_TAG}" \
    -t "${IMAGE_REGISTRY}/uepi/worker:latest" \
    -f apps/worker/Dockerfile .

echo "📤 Pushing Worker image..."
docker push "${IMAGE_REGISTRY}/uepi/worker:${IMAGE_TAG}"
docker push "${IMAGE_REGISTRY}/uepi/worker:latest"

# Build and push Web image
echo ""
echo "📦 Building Web image..."
docker build \
    --platform linux/amd64 \
    -t "${IMAGE_REGISTRY}/uepi/web:${IMAGE_TAG}" \
    -t "${IMAGE_REGISTRY}/uepi/web:latest" \
    -f apps/web/Dockerfile .

echo "📤 Pushing Web image..."
docker push "${IMAGE_REGISTRY}/uepi/web:${IMAGE_TAG}"
docker push "${IMAGE_REGISTRY}/uepi/web:latest"

# Update Helm deployment
echo ""
echo "🚀 Updating Helm deployment..."

# Create temporary values file
cat > /tmp/uepi-update-values.yaml <<EOF
api:
  image:
    repository: ${IMAGE_REGISTRY}/uepi/api
    tag: ${IMAGE_TAG}

worker:
  image:
    repository: ${IMAGE_REGISTRY}/uepi/worker
    tag: ${IMAGE_TAG}

web:
  image:
    repository: ${IMAGE_REGISTRY}/uepi/web
    tag: ${IMAGE_TAG}
EOF

# Upgrade Helm release
helm upgrade --install uepi ./infra/helm/uepi \
    --namespace "$NAMESPACE" \
    --create-namespace \
    --values /tmp/uepi-update-values.yaml \
    --wait --timeout=10m

# Wait for pods to be ready
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l component=api -n "$NAMESPACE" --timeout=300s || true
kubectl wait --for=condition=ready pod -l component=worker -n "$NAMESPACE" --timeout=300s || true
kubectl wait --for=condition=ready pod -l component=web -n "$NAMESPACE" --timeout=300s || true

# Show pod status
echo ""
echo "📊 Pod Status:"
kubectl get pods -n "$NAMESPACE"

# Show ingress
echo ""
echo "🌐 Ingress:"
kubectl get ingress -n "$NAMESPACE" || echo "No ingress found"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Summary:"
echo "  API Image: ${IMAGE_REGISTRY}/uepi/api:${IMAGE_TAG}"
echo "  Worker Image: ${IMAGE_REGISTRY}/uepi/worker:${IMAGE_TAG}"
echo "  Web Image: ${IMAGE_REGISTRY}/uepi/web:${IMAGE_TAG}"
echo ""
echo "🔄 To rollback, use:"
echo "  helm rollback uepi -n $NAMESPACE"
echo ""
echo "📝 To check logs:"
echo "  kubectl logs -f deployment/uepi-api -n $NAMESPACE"
echo "  kubectl logs -f deployment/uepi-web -n $NAMESPACE"
echo ""

