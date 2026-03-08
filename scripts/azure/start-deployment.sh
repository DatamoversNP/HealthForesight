#!/bin/bash
# Start Azure deployment - this will create real resources!

set -e

echo "=========================================="
echo "🚀 UEPI Azure Deployment"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: This will create Azure resources"
echo "   Estimated monthly cost: $500-900"
echo "   Deployment time: 15-30 minutes"
echo ""
read -p "Do you want to proceed? (type 'yes' to continue): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Verify prerequisites
echo ""
echo "Verifying prerequisites..."

command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI not found"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm not found"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform not found"; exit 1; }

echo "✅ All tools installed"

# Check Azure login
az account show >/dev/null 2>&1 || {
    echo "Please login to Azure..."
    az login
}

SUBSCRIPTION=$(az account show --query name -o tsv)
echo "✅ Using subscription: $SUBSCRIPTION"
echo ""

# Set configuration
RESOURCE_GROUP="uepi-rg-$(date +%s | cut -c6-)"
LOCATION="eastus"
AKS_NAME="uepi-aks-$(date +%s | cut -c6-)"
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo "Deployment Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  AKS Cluster: $AKS_NAME"
echo "  PostgreSQL Password: [auto-generated]"
echo ""

read -p "Use these settings? (yes/no): " USE_DEFAULTS
if [ "$USE_DEFAULTS" != "yes" ]; then
    read -p "Resource group name: " RESOURCE_GROUP
    read -p "Azure region [eastus]: " LOCATION
    LOCATION=${LOCATION:-eastus}
    read -p "AKS cluster name: " AKS_NAME
    read -sp "PostgreSQL password (min 8 chars): " POSTGRES_PASSWORD
    echo ""
fi

# Initialize Terraform
echo ""
echo "📦 Initializing Terraform..."
cd infra/terraform/envs/azure

# Create terraform.tfvars
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

echo "✅ Configuration file created"

# Initialize and plan
terraform init
echo ""
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan

echo ""
echo "⚠️  Review the plan above carefully!"
read -p "Apply this plan? (type 'yes' to continue): " APPLY

if [ "$APPLY" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "🏗️  Creating Azure infrastructure..."
echo "This will take 15-30 minutes. Please wait..."
echo ""

terraform apply tfplan

echo ""
echo "✅ Infrastructure created successfully!"
echo ""
echo "Getting connection details..."

# Get outputs
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
echo "🔧 Configuring Kubernetes..."
az aks get-credentials --resource-group "${RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing

echo ""
echo "📝 Creating Kubernetes resources..."
kubectl create namespace uepi-prod --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
echo "Creating secrets..."
kubectl create secret generic uepi-database-secret \
    --from-literal=url="${POSTGRES_CONNECTION}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

REDIS_URL="rediss://:${POSTGRES_PASSWORD}@${REDIS_HOSTNAME}:${REDIS_SSL_PORT}/0"
kubectl create secret generic uepi-redis-secret \
    --from-literal=url="${REDIS_URL}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic uepi-object-storage-secret \
    --from-literal=access-key="${STORAGE_ACCOUNT}" \
    --from-literal=secret-key="${STORAGE_KEY}" \
    -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "⚠️  Azure AD Setup Required"
echo "   For OIDC authentication, you need to set up Azure AD"
echo "   Run: ./scripts/azure/setup-azure-ad.sh"
echo ""
read -p "Enter Azure AD OIDC issuer URL (or press Enter to skip): " OIDC_ISSUER
if [ -n "$OIDC_ISSUER" ]; then
    kubectl create secret generic uepi-oidc-secret \
        --from-literal=issuer="${OIDC_ISSUER}" \
        -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -
    echo "✅ OIDC secret created"
else
    echo "⚠️  Skipping OIDC setup - you can add it later"
fi

echo ""
echo "📦 Preparing Helm deployment..."
echo ""
echo "⚠️  IMPORTANT: You need Docker images!"
echo "   Options:"
echo "   1. Build and push images now (will take time)"
echo "   2. Use placeholder images and update later"
echo ""
read -p "Build Docker images now? (yes/no): " BUILD_IMAGES

if [ "$BUILD_IMAGES" = "yes" ]; then
    echo ""
    echo "Building Docker images..."
    docker build -t uepi/api:latest -f apps/api/Dockerfile . || echo "⚠️  Build failed - you can build later"
    docker build -t uepi/worker:latest -f apps/worker/Dockerfile . || echo "⚠️  Build failed - you can build later"
    docker build -t uepi/web:latest -f apps/web/Dockerfile . || echo "⚠️  Build failed - you can build later"
    echo ""
    echo "⚠️  Note: You need to push these to a container registry"
    echo "   Create ACR: az acr create --resource-group $RESOURCE_GROUP --name uepiregistry --sku Basic"
    echo "   Then push: az acr login --name uepiregistry && docker push uepiregistry.azurecr.io/uepi/api:latest"
fi

echo ""
echo "🚀 Deploying UEPI with Helm..."
echo ""

# Create custom values
cat > /tmp/uepi-values.yaml <<EOF
api:
  image:
    repository: uepi/api
    tag: latest
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"

worker:
  image:
    repository: uepi/worker
    tag: latest
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"

web:
  image:
    repository: uepi/web
    tag: latest
EOF

helm upgrade --install uepi ./infra/helm/uepi \
    --namespace uepi-prod \
    --create-namespace \
    --values /tmp/uepi-values.yaml \
    --wait --timeout=10m || echo "⚠️  Deployment may need image registry configuration"

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📊 Deployment Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  AKS Cluster: $AKS_CLUSTER_NAME"
echo "  PostgreSQL: $POSTGRES_FQDN"
echo "  Redis: $REDIS_HOSTNAME"
echo "  Storage: $STORAGE_ACCOUNT"
echo ""
echo "📋 Next Steps:"
echo "  1. Check deployment status:"
echo "     kubectl get pods -n uepi-prod"
echo ""
echo "  2. Run database migrations:"
echo "     kubectl exec -it deployment/uepi-api -n uepi-prod -- alembic upgrade head"
echo ""
echo "  3. Get ingress IP:"
echo "     kubectl get ingress -n uepi-prod"
echo ""
echo "  4. Configure DNS to point to ingress IP"
echo ""
echo "  5. Set up Azure AD (if not done):"
echo "     ./scripts/azure/setup-azure-ad.sh"
echo ""
echo "📝 Save these details:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  PostgreSQL Password: $POSTGRES_PASSWORD"
echo ""
echo "✅ Deployment complete! Check status with: kubectl get all -n uepi-prod"

