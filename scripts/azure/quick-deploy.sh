#!/bin/bash
# Quick deployment script with minimal prompts
# This will create real Azure resources and incur costs!

set -e

echo "=========================================="
echo "UEPI Azure Deployment - Quick Start"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will create Azure resources that cost money!"
echo "   Estimated cost: ~$500-900/month"
echo ""
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Check prerequisites
echo ""
echo "Checking prerequisites..."

MISSING=0
command -v az >/dev/null 2>&1 || { echo "✗ Azure CLI not found"; MISSING=1; }
command -v kubectl >/dev/null 2>&1 || { echo "✗ kubectl not found"; MISSING=1; }
command -v helm >/dev/null 2>&1 || { echo "✗ Helm not found"; MISSING=1; }
command -v terraform >/dev/null 2>&1 || { echo "✗ Terraform not found"; MISSING=1; }

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Please install missing tools:"
    echo "  - Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli"
    echo "  - kubectl: https://kubernetes.io/docs/tasks/tools/"
    echo "  - Helm: https://helm.sh/docs/intro/install/"
    echo "  - Terraform: https://www.terraform.io/downloads"
    exit 1
fi

echo "✓ All prerequisites met"

# Check Azure login
az account show >/dev/null 2>&1 || {
    echo "Please login to Azure..."
    az login
}

SUBSCRIPTION=$(az account show --query name -o tsv)
echo "✓ Using Azure subscription: $SUBSCRIPTION"

# Set defaults
RESOURCE_GROUP="uepi-rg-$(date +%s)"
LOCATION="eastus"
AKS_NAME="uepi-aks-$(date +%s)"
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  AKS Cluster: $AKS_NAME"
echo "  PostgreSQL Password: [generated]"
echo ""

read -p "Use these defaults? (yes/no): " USE_DEFAULTS
if [ "$USE_DEFAULTS" != "yes" ]; then
    read -p "Resource group name: " RESOURCE_GROUP
    read -p "Azure region [eastus]: " LOCATION
    LOCATION=${LOCATION:-eastus}
    read -p "AKS cluster name: " AKS_NAME
    read -sp "PostgreSQL password: " POSTGRES_PASSWORD
    echo ""
fi

# Create terraform.tfvars
cd infra/terraform/envs/azure
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

echo ""
echo "Starting Terraform deployment..."
echo "This will take 15-30 minutes..."
echo ""

terraform init
terraform plan -out=tfplan

echo ""
read -p "Apply Terraform plan? (yes/no): " APPLY
if [ "$APPLY" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

terraform apply tfplan

echo ""
echo "✓ Infrastructure created!"
echo ""
echo "Getting outputs..."
AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name)
POSTGRES_FQDN=$(terraform output -raw postgres_fqdn)
POSTGRES_CONNECTION=$(terraform output -raw postgres_connection_string)
REDIS_HOSTNAME=$(terraform output -raw redis_hostname)
REDIS_SSL_PORT=$(terraform output -raw redis_ssl_port)
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)
STORAGE_KEY=$(terraform output -raw storage_primary_access_key)
STORAGE_ENDPOINT=$(terraform output -raw storage_blob_endpoint)

cd ../../../../

echo ""
echo "Configuring kubectl..."
az aks get-credentials --resource-group "${RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing

echo ""
echo "Creating namespace and secrets..."
kubectl create namespace uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
kubectl create secret generic uepi-database-secret \
    --from-literal=url="${POSTGRES_CONNECTION}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Note: Redis password is same as postgres in this setup (you may want to change this)
REDIS_URL="rediss://:${POSTGRES_PASSWORD}@${REDIS_HOSTNAME}:${REDIS_SSL_PORT}/0"
kubectl create secret generic uepi-redis-secret \
    --from-literal=url="${REDIS_URL}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic uepi-object-storage-secret \
    --from-literal=access-key="${STORAGE_ACCOUNT}" \
    --from-literal=secret-key="${STORAGE_KEY}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "⚠️  Note: You need to set up Azure AD for OIDC authentication"
echo "   Run: ./scripts/azure/setup-azure-ad.sh"
read -p "Enter Azure AD OIDC issuer URL (or press Enter to skip): " OIDC_ISSUER
if [ -n "$OIDC_ISSUER" ]; then
    kubectl create secret generic uepi-oidc-secret \
        --from-literal=issuer="${OIDC_ISSUER}" \
        -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -
fi

echo ""
echo "⚠️  Note: You need to build and push Docker images first"
echo "   Or update Helm values with your image registry"
read -p "Press Enter to continue with deployment (images must exist)..."

echo ""
echo "Deploying with Helm..."
helm upgrade --install uepi ./infra/helm/uepi \
    --namespace uepi-prod \
    --create-namespace \
    --set api.image.repository=uepi/api \
    --set api.image.tag=latest \
    --set worker.image.repository=uepi/worker \
    --set worker.image.tag=latest \
    --set web.image.repository=uepi/web \
    --set web.image.tag=latest \
    --set api.env.OBJECT_STORAGE_ENDPOINT="${STORAGE_ENDPOINT}" \
    --set worker.env.OBJECT_STORAGE_ENDPOINT="${STORAGE_ENDPOINT}" \
    --wait --timeout=10m

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Build and push Docker images to your registry"
echo "2. Update Helm values with correct image paths"
echo "3. Run database migrations:"
echo "   kubectl exec -it deployment/uepi-api -n uepi-prod -- alembic upgrade head"
echo "4. Get ingress IP: kubectl get ingress -n uepi-prod"
echo "5. Configure DNS to point to ingress IP"
echo ""
echo "Check status:"
echo "  kubectl get pods -n uepi-prod"
echo "  kubectl get svc -n uepi-prod"
echo "  helm status uepi -n uepi-prod"

