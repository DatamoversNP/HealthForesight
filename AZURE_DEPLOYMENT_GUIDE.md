# Azure Deployment Guide - Complete Platform Deployment

## Overview

This guide covers deploying the HealthForesight platform to Azure using multiple approaches, from simple to production-ready.

## Architecture Overview

The platform consists of:

1. **API Service** (FastAPI) - Backend API
2. **Web Application** (React) - Frontend
3. **Worker Service** (Python) - Background jobs
4. **File Storage** - Azure File Storage (now supported)
5. **Redis** (optional) - For queues/caching

## Deployment Approaches

### Option 1: Simple - Azure App Service (Recommended for MVP)

**Best for**: Quick deployment, easy management, cost-effective

**Services**:
- **API**: Azure App Service (Python)
- **Web**: Azure Static Web Apps or App Service
- **Storage**: Azure File Storage
- **Optional**: Azure Cache for Redis

**Pros**:
- ✅ Simplest to deploy and manage
- ✅ Auto-scaling built-in
- ✅ Easy CI/CD integration
- ✅ Cost-effective for small-medium workloads
- ✅ Built-in SSL and domains

**Cons**:
- ⚠️ Less control than containers
- ⚠️ Limited customization options

### Option 2: Containerized - Azure Container Apps

**Best for**: Containerized apps, simple orchestration

**Services**:
- **API**: Azure Container Apps (Docker)
- **Web**: Azure Container Apps or Static Web Apps
- **Worker**: Azure Container Apps
- **Storage**: Azure File Storage
- **Optional**: Azure Cache for Redis

**Pros**:
- ✅ Easy container deployment
- ✅ Auto-scaling and revision management
- ✅ Built-in load balancing
- ✅ Serverless-like scaling

**Cons**:
- ⚠️ Newer service (less mature)
- ⚠️ Some Kubernetes features missing

### Option 3: Full Kubernetes - Azure Kubernetes Service (AKS)

**Best for**: Production, complex requirements, maximum control

**Services**:
- **API**: AKS Pods (Docker)
- **Web**: AKS Pods or Azure Front Door + Storage
- **Worker**: AKS Pods
- **Storage**: Azure File Storage (via CSI driver)
- **Optional**: Azure Cache for Redis

**Pros**:
- ✅ Full Kubernetes control
- ✅ Advanced orchestration
- ✅ Can use existing Helm charts
- ✅ Best for production workloads

**Cons**:
- ⚠️ More complex to manage
- ⚠️ Higher operational overhead
- ⚠️ More expensive

## Recommended Approach: Azure App Service (Simple)

Since you want to keep it simple and file-based, **Azure App Service** is recommended.

## Step-by-Step Deployment: Azure App Service

### Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed: `az --version`
3. **Docker** (for building images, optional)
4. **Git** (for deployment)

### Step 1: Set Up Azure Resources

#### 1.1 Create Resource Group

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"  # Or your preferred region

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

#### 1.2 Create Azure Storage Account (for File Share)

```bash
STORAGE_ACCOUNT="healthforesight$(date +%s)"  # Must be globally unique
AZURE_STORAGE_FILE_SHARE_NAME="healthforesight-data"

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create file share
az storage share create \
  --name $AZURE_STORAGE_FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

echo "Storage Account: $STORAGE_ACCOUNT"
echo "Storage Key: $STORAGE_KEY"
echo "File Share: $AZURE_STORAGE_FILE_SHARE_NAME"
```

#### 1.3 Create Azure Cache for Redis (Optional)

```bash
REDIS_NAME="healthforesight-redis"

az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0

# Get Redis connection string
REDIS_HOST=$(az redis show \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query hostName -o tsv)

REDIS_KEY=$(az redis list-keys \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query primaryKey -o tsv)
```

### Step 2: Deploy API Service

#### 2.1 Create App Service Plan

```bash
APP_SERVICE_PLAN="healthforesight-plan"

az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1  # Basic tier (adjust as needed)
  --is-linux
```

#### 2.2 Create API App Service

```bash
API_APP_NAME="healthforesight-api-$(date +%s)"  # Must be globally unique

az webapp create \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11"
```

#### 2.3 Configure API App Service

```bash
# Set Azure File Storage environment variables
az webapp config appsettings set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    AZURE_STORAGE_FILE_SHARE_NAME=$AZURE_STORAGE_FILE_SHARE_NAME \
    USE_FILE_STORAGE=true \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Set port (FastAPI default)
az webapp config set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000"
```

#### 2.4 Deploy API Code

**Option A: Deploy from Local (using ZIP)**

```bash
cd apps/api

# Create deployment package
poetry build
poetry export -f requirements.txt --output requirements.txt

# Install dependencies locally
poetry install --no-dev

# Create ZIP
zip -r deploy.zip . -x "*.git*" -x "*.venv*" -x "*__pycache__*"

# Deploy to Azure
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src deploy.zip
```

**Option B: Deploy from GitHub (recommended)**

```bash
# Configure GitHub deployment
az webapp deployment source config \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url https://github.com/yourusername/healthforesight \
  --branch main \
  --manual-integration
```

#### 2.5 Get API URL

```bash
API_URL=$(az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName -o tsv)

echo "API URL: https://$API_URL"
```

### Step 3: Deploy Web Application

#### 3.1 Create Static Web App (Recommended)

```bash
WEB_APP_NAME="healthforesight-web"

az staticwebapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Free  # Or Standard for production
```

#### 3.2 Configure Static Web App

```bash
# Set API URL in app settings
az staticwebapp appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting-names \
    VITE_API_URL=https://$API_URL \
    VITE_API_BASE_URL=https://$API_URL/api/v1
```

#### 3.3 Build and Deploy Web App

```bash
cd apps/web

# Build for production
npm install
npm run build

# Deploy to Static Web App
az staticwebapp deploy \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --app-location "apps/web" \
  --output-location "dist"
```

### Step 4: Configure CORS

```bash
# Allow web app to access API
az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_APP_NAME.azurestaticapps.net"
```

### Step 5: Test Deployment

```bash
# Check API health
curl https://$API_URL/health

# Check API docs
curl https://$API_URL/docs

# Open web app
az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv
```

## Alternative: Azure Container Apps (Containerized)

If you prefer containerized deployment:

### Step 1: Build and Push Docker Images

```bash
# Login to Azure Container Registry
ACR_NAME="healthforesightacr$(date +%s)"
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic

az acr login --name $ACR_NAME

# Build and push API image
cd apps/api
docker build -t $ACR_NAME.azurecr.io/api:latest .
docker push $ACR_NAME.azurecr.io/api:latest

# Build and push Web image
cd ../web
docker build -t $ACR_NAME.azurecr.io/web:latest .
docker push $ACR_NAME.azurecr.io/web:latest
```

### Step 2: Create Container Apps Environment

```bash
az containerapp env create \
  --name healthforesight-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### Step 3: Create Container Apps

```bash
# Create API container app
az containerapp create \
  --name healthforesight-api \
  --resource-group $RESOURCE_GROUP \
  --environment healthforesight-env \
  --image $ACR_NAME.azurecr.io/api:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    AZURE_STORAGE_FILE_SHARE_NAME=$AZURE_STORAGE_FILE_SHARE_NAME

# Create Web container app
az containerapp create \
  --name healthforesight-web \
  --resource-group $RESOURCE_GROUP \
  --environment healthforesight-env \
  --image $ACR_NAME.azurecr.io/web:latest \
  --target-port 80 \
  --ingress external \
  --env-vars \
    VITE_API_URL=https://healthforesight-api.azurecontainerapps.io
```

## Alternative: Azure Kubernetes Service (AKS)

For production Kubernetes deployment:

### Step 1: Create AKS Cluster

```bash
AKS_NAME="healthforesight-aks"

az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME \
  --node-count 2 \
  --enable-managed-identity \
  --generate-ssh-keys
```

### Step 2: Configure kubectl

```bash
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME
```

### Step 3: Install Azure File CSI Driver

```bash
# Create storage class for Azure Files
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azurefile
provisioner: file.csi.azure.com
parameters:
  skuName: Standard_LRS
EOF
```

### Step 4: Deploy with Helm

```bash
cd infra/helm/uepi

# Update values for Azure
helm upgrade --install healthforesight . \
  --namespace healthforesight \
  --create-namespace \
  --values values-azure.yaml \
  --set azure.storageAccount=$STORAGE_ACCOUNT \
  --set azure.storageKey=$STORAGE_KEY \
  --set azure.fileShareName=$AZURE_STORAGE_FILE_SHARE_NAME
```

## Configuration Summary

### Environment Variables for Azure

```bash
# Azure File Storage
USE_AZURE_FILE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
AZURE_STORAGE_ACCOUNT_KEY=<storage-key>
AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# API URL (for web app)
VITE_API_URL=https://<api-app-name>.azurewebsites.net
VITE_API_BASE_URL=https://<api-app-name>.azurewebsites.net/api/v1
```

## Deployment Scripts

I'll create deployment scripts for each approach in the next section.

## Next Steps

1. ✅ Choose deployment approach (recommend App Service for simplicity)
2. ⏭️ Set up Azure resources
3. ⏭️ Deploy API service
4. ⏭️ Deploy web application
5. ⏭️ Configure CORS and networking
6. ⏭️ Test deployment
7. ⏭️ Set up CI/CD

## Cost Estimation

### Azure App Service (Simple Approach)

- **API App Service**: ~$13-55/month (B1-B2 tier)
- **Web Static Web App**: Free (or ~$9/month Standard)
- **Azure File Storage**: ~$0.06/GB/month
- **Azure Cache for Redis**: ~$16/month (Basic C0)
- **Total**: ~$30-80/month (depending on usage)

### Azure Container Apps

- **Container Apps**: Pay per use (~$0.000012/vCPU-second)
- **Azure File Storage**: Same as above
- **Total**: Variable based on usage

### Azure Kubernetes Service (AKS)

- **AKS Cluster**: ~$73/month (2 nodes, Standard_D2s_v3)
- **Azure File Storage**: Same as above
- **Total**: ~$100+/month

## Troubleshooting

### API not starting

```bash
# Check logs
az webapp log tail --name $API_APP_NAME --resource-group $RESOURCE_GROUP

# Check app settings
az webapp config appsettings list --name $API_APP_NAME --resource-group $RESOURCE_GROUP
```

### File storage not working

```bash
# Verify storage account
az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP

# Check file share
az storage share list --account-name $STORAGE_ACCOUNT --account-key $STORAGE_KEY
```

### CORS issues

```bash
# Add web app to CORS
az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_APP_NAME.azurestaticapps.net"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ secrets.AZURE_API_APP_NAME }}
          publish-profile: ${{ secrets.AZURE_API_PUBLISH_PROFILE }}
          
  deploy-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
```

## Summary

✅ **Simple Approach**: Azure App Service (recommended)
✅ **Containerized**: Azure Container Apps
✅ **Full Kubernetes**: Azure Kubernetes Service (AKS)
✅ **File Storage**: Azure File Storage (now supported)
✅ **All approaches support file-based architecture**

Choose the approach that best fits your needs and complexity requirements!
