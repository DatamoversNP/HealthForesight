#!/bin/bash
# Setup script for creating Kubernetes secrets
# This script helps create all required secrets for HealthForesight deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}HealthForesight Kubernetes Secrets Setup${NC}"
echo "=============================================="

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl not found. Please install it.${NC}" >&2; exit 1; }
command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI not found. Please install it.${NC}" >&2; exit 1; }

# Check Azure login
az account show >/dev/null 2>&1 || { 
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
}

# Get AKS cluster info
if [ -z "$AKS_RESOURCE_GROUP" ]; then
    read -p "Enter AKS resource group name: " AKS_RESOURCE_GROUP
fi

if [ -z "$AKS_CLUSTER_NAME" ]; then
    read -p "Enter AKS cluster name: " AKS_CLUSTER_NAME
fi

# Get kubectl credentials
echo -e "${YELLOW}Configuring kubectl...${NC}"
az aks get-credentials --resource-group "${AKS_RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing

# Get namespace
read -p "Enter namespace [healthforesight-prod]: " NAMESPACE
NAMESPACE=${NAMESPACE:-healthforesight-prod}

# Create namespace
echo -e "${YELLOW}Creating namespace ${NAMESPACE}...${NC}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Get database connection string
echo ""
echo -e "${YELLOW}Database Configuration${NC}"
read -p "Enter PostgreSQL connection string (or press Enter to skip): " DB_URL

if [ -n "$DB_URL" ]; then
    echo -e "${YELLOW}Creating database secret...${NC}"
    kubectl create secret generic healthforesight-database-secret \
        --from-literal=url="${DB_URL}" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ Database secret created${NC}"
fi

# Get Redis connection string
echo ""
echo -e "${YELLOW}Redis Configuration${NC}"
read -p "Enter Redis connection string (or press Enter to skip): " REDIS_URL

if [ -n "$REDIS_URL" ]; then
    echo -e "${YELLOW}Creating Redis secret...${NC}"
    kubectl create secret generic healthforesight-redis-secret \
        --from-literal=url="${REDIS_URL}" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ Redis secret created${NC}"
fi

# Get storage account info
echo ""
echo -e "${YELLOW}Object Storage Configuration${NC}"
read -p "Enter storage account name (or press Enter to skip): " STORAGE_ACCOUNT
read -p "Enter storage account key (or press Enter to skip): " STORAGE_KEY

if [ -n "$STORAGE_ACCOUNT" ] && [ -n "$STORAGE_KEY" ]; then
    echo -e "${YELLOW}Creating storage secret...${NC}"
    kubectl create secret generic healthforesight-object-storage-secret \
        --from-literal=access-key="${STORAGE_ACCOUNT}" \
        --from-literal=secret-key="${STORAGE_KEY}" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ Storage secret created${NC}"
fi

# OIDC configuration (optional)
echo ""
echo -e "${YELLOW}OIDC Configuration (Optional)${NC}"
read -p "Enter OIDC issuer URL (or press Enter to skip): " OIDC_ISSUER

if [ -n "$OIDC_ISSUER" ]; then
    echo -e "${YELLOW}Creating OIDC secret...${NC}"
    kubectl create secret generic healthforesight-oidc-secret \
        --from-literal=issuer="${OIDC_ISSUER}" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ OIDC secret created${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}✅ Secrets setup complete!${NC}"
echo ""
echo "Created secrets in namespace: ${NAMESPACE}"
echo ""
echo "List secrets:"
kubectl get secrets -n "${NAMESPACE}"
echo ""
echo "Next steps:"
echo "  1. Verify secrets: kubectl get secrets -n ${NAMESPACE}"
echo "  2. Deploy application: helm upgrade --install healthforesight ./infra/helm/uepi -n ${NAMESPACE}"
echo ""

