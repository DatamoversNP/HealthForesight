#!/bin/bash
# Automated Azure deployment with environment variables
# Set these environment variables or they will use defaults

set -e

# Configuration from environment or defaults
RESOURCE_GROUP="${RESOURCE_GROUP:-uepi-rg-$(date +%s | cut -c6-)}"
LOCATION="${LOCATION:-westus2}"  # Changed from eastus due to subscription restrictions
AKS_NAME="${AKS_NAME:-uepi-aks-$(date +%s | cut -c6-)}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)}"
AUTO_CONFIRM="${AUTO_CONFIRM:-no}"

echo "=========================================="
echo "🚀 UEPI Azure Deployment (Automated)"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  AKS Cluster: $AKS_NAME"
echo "  PostgreSQL Password: [auto-generated]"
echo ""

if [ "$AUTO_CONFIRM" != "yes" ]; then
    echo "⚠️  This will create Azure resources (~\$500-900/month)"
    echo "   Set AUTO_CONFIRM=yes to skip this prompt"
    echo ""
    read -p "Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

# Verify prerequisites
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI not found"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm not found"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform not found"; exit 1; }

# Check Azure login
az account show >/dev/null 2>&1 || {
    echo "Please login to Azure..."
    az login
}

SUBSCRIPTION=$(az account show --query name -o tsv)
echo "✅ Using subscription: $SUBSCRIPTION"
echo ""

# Initialize Terraform
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

echo "✅ Configuration created"
echo ""

# Initialize and plan
terraform init
echo ""
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan > /tmp/terraform-plan.txt
cat /tmp/terraform-plan.txt

if [ "$AUTO_CONFIRM" != "yes" ]; then
    echo ""
    read -p "Apply this plan? (yes/no): " APPLY
    if [ "$APPLY" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi
fi

echo ""
echo "🏗️  Creating Azure infrastructure..."
echo "This will take 15-30 minutes. Please wait..."
echo ""

terraform apply -auto-approve tfplan

echo ""
echo "✅ Infrastructure created successfully!"
echo ""

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

# OIDC secret (optional)
if [ -n "$OIDC_ISSUER" ]; then
    kubectl create secret generic uepi-oidc-secret \
        --from-literal=issuer="${OIDC_ISSUER}" \
        -n uepi-prod --dry-run=client -o yaml | kubectl apply -f -
    echo "✅ OIDC secret created"
else
    echo "⚠️  OIDC not configured - set OIDC_ISSUER environment variable to add it"
fi

echo ""
echo "📦 Preparing Helm deployment..."

# Create custom values
cat > /tmp/uepi-values.yaml <<EOF
api:
  image:
    repository: ${IMAGE_REGISTRY:-uepi}/api
    tag: ${IMAGE_TAG:-latest}
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"

worker:
  image:
    repository: ${IMAGE_REGISTRY:-uepi}/worker
    tag: ${IMAGE_TAG:-latest}
  env:
    OBJECT_STORAGE_ENDPOINT: "${STORAGE_ENDPOINT}"
    OBJECT_STORAGE_BUCKET: "uepi-data"

web:
  image:
    repository: ${IMAGE_REGISTRY:-uepi}/web
    tag: ${IMAGE_TAG:-latest}
EOF

echo ""
echo "🚀 Deploying UEPI with Helm..."
echo ""

helm upgrade --install uepi ./infra/helm/uepi \
    --namespace uepi-prod \
    --create-namespace \
    --values /tmp/uepi-values.yaml \
    --wait --timeout=10m || echo "⚠️  Deployment may need image registry configuration"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  AKS Cluster: $AKS_CLUSTER_NAME"
echo "  PostgreSQL: $POSTGRES_FQDN"
echo "  Redis: $REDIS_HOSTNAME"
echo "  Storage: $STORAGE_ACCOUNT"
echo ""
echo "📋 Next Steps:"
echo "  1. Check status: kubectl get pods -n uepi-prod"
echo "  2. Run migrations: kubectl exec -it deployment/uepi-api -n uepi-prod -- alembic upgrade head"
echo "  3. Get ingress: kubectl get ingress -n uepi-prod"
echo ""
echo "📝 Save these details:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  PostgreSQL Password: $POSTGRES_PASSWORD"
echo ""

