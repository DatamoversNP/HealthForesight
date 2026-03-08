#!/bin/bash
# Azure deployment script for UEPI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}UEPI Azure Deployment Script${NC}"
echo "================================"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v az >/dev/null 2>&1 || { echo -e "${RED}Azure CLI not found. Please install it.${NC}" >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl not found. Please install it.${NC}" >&2; exit 1; }
command -v helm >/dev/null 2>&1 || { echo -e "${RED}Helm not found. Please install it.${NC}" >&2; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Terraform not found. Please install it.${NC}" >&2; exit 1; }

# Check Azure login
echo -e "${YELLOW}Checking Azure login...${NC}"
az account show >/dev/null 2>&1 || { 
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
}

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}Using subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})${NC}"

# Set variables
read -p "Enter resource group name [uepi-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-uepi-rg}

read -p "Enter Azure region [East US]: " LOCATION
LOCATION=${LOCATION:-East US}

read -p "Enter AKS cluster name [uepi-aks]: " AKS_NAME
AKS_NAME=${AKS_NAME:-uepi-aks}

read -sp "Enter PostgreSQL admin password: " POSTGRES_PASSWORD
echo ""

# Step 1: Create infrastructure with Terraform
echo -e "${GREEN}Step 1: Creating Azure infrastructure with Terraform...${NC}"
cd infra/terraform/envs/azure

# Initialize Terraform
terraform init

# Create terraform.tfvars if it doesn't exist
if [ ! -f terraform.tfvars ]; then
    cat > terraform.tfvars <<EOF
resource_group_name = "${RESOURCE_GROUP}"
location            = "${LOCATION}"
environment         = "production"
aks_cluster_name    = "${AKS_NAME}"
postgres_server_name = "uepi-postgres"
redis_cache_name    = "uepi-redis"
storage_account_name = "uepistorage"
admin_username      = "uepiadmin"
admin_password      = "${POSTGRES_PASSWORD}"
EOF
    echo -e "${GREEN}Created terraform.tfvars${NC}"
fi

# Plan and apply
terraform plan -out=tfplan
read -p "Apply Terraform plan? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply tfplan
    
    # Get outputs
    AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
    POSTGRES_FQDN=$(terraform output -raw postgres_fqdn)
    POSTGRES_CONNECTION=$(terraform output -raw postgres_connection_string)
    REDIS_HOSTNAME=$(terraform output -raw redis_hostname)
    REDIS_PORT=$(terraform output -raw redis_port)
    REDIS_SSL_PORT=$(terraform output -raw redis_ssl_port)
    STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)
    STORAGE_KEY=$(terraform output -raw storage_primary_access_key)
    STORAGE_ENDPOINT=$(terraform output -raw storage_blob_endpoint)
    
    echo -e "${GREEN}Infrastructure created successfully!${NC}"
else
    echo -e "${YELLOW}Terraform apply cancelled${NC}"
    exit 1
fi

cd ../../../../

# Step 2: Configure kubectl
echo -e "${GREEN}Step 2: Configuring kubectl...${NC}"
az aks get-credentials --resource-group "${RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing

# Step 3: Create namespace
echo -e "${GREEN}Step 3: Creating Kubernetes namespace...${NC}"
kubectl create namespace uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Create secrets
echo -e "${GREEN}Step 4: Creating Kubernetes secrets...${NC}"

# Database secret
kubectl create secret generic uepi-database-secret \
    --from-literal=url="${POSTGRES_CONNECTION}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Redis secret (using SSL port)
REDIS_URL="rediss://:${POSTGRES_PASSWORD}@${REDIS_HOSTNAME}:${REDIS_SSL_PORT}/0"
kubectl create secret generic uepi-redis-secret \
    --from-literal=url="${REDIS_URL}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Object storage secret
kubectl create secret generic uepi-object-storage-secret \
    --from-literal=access-key="${STORAGE_ACCOUNT}" \
    --from-literal=secret-key="${STORAGE_KEY}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# OIDC secret (Azure AD)
read -p "Enter Azure AD OIDC issuer URL: " OIDC_ISSUER
kubectl create secret generic uepi-oidc-secret \
    --from-literal=issuer="${OIDC_ISSUER}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}Secrets created${NC}"

# Step 5: Update Helm values
echo -e "${GREEN}Step 5: Preparing Helm values...${NC}"
cat > /tmp/uepi-azure-values.yaml <<EOF
api:
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"
  ingress:
    hosts:
      - host: api.uepi.yourdomain.com
        paths:
          - path: /
            pathType: Prefix

worker:
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"

web:
  env:
    VITE_API_URL: "https://api.uepi.yourdomain.com"
  ingress:
    hosts:
      - host: uepi.yourdomain.com
        paths:
          - path: /
            pathType: Prefix
EOF

echo -e "${YELLOW}Please update the domain names in /tmp/uepi-azure-values.yaml${NC}"
read -p "Press Enter to continue after updating..."

# Step 6: Deploy with Helm
echo -e "${GREEN}Step 6: Deploying UEPI with Helm...${NC}"
helm upgrade --install uepi ./infra/helm/uepi \
    --namespace uepi-prod \
    --values ./infra/helm/uepi/values-azure.yaml \
    --values /tmp/uepi-azure-values.yaml \
    --wait

# Step 7: Run database migrations
echo -e "${GREEN}Step 7: Running database migrations...${NC}"
kubectl wait --for=condition=ready pod -l component=api -n uepi-prod --timeout=300s
kubectl exec -it deployment/uepi-api -n uepi-prod -- alembic upgrade head

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Configure your DNS to point to the ingress IP"
echo "2. Set up SSL certificates (cert-manager)"
echo "3. Configure Azure AD for OIDC authentication"
echo "4. Monitor the deployment: kubectl get pods -n uepi-prod"

