# Azure Deployment - Step-by-Step Guide

## Overview

This guide walks you through deploying the HealthForesight platform to Azure using **Azure App Service** (simplest approach).

## Prerequisites

1. **Azure Account** with active subscription
   - Sign up at: https://azure.microsoft.com/free/
   - Free tier includes $200 credit

2. **Azure CLI** installed
   ```bash
   # macOS
   brew install azure-cli
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Windows
   # Download from: https://aka.ms/installazurecliwindows
   ```

3. **Verify Azure CLI**
   ```bash
   az --version
   ```

4. **Git** (for deployment)
   ```bash
   git --version
   ```

## Step 1: Login to Azure

```bash
# Login to Azure
az login

# List your subscriptions
az account list --output table

# Set your subscription (if you have multiple)
az account set --subscription "Your Subscription Name or ID"
```

## Step 2: Run Automated Deployment Script

We have an automated script that will set up everything:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
chmod +x scripts/azure/deploy-app-service.sh
./scripts/azure/deploy-app-service.sh
```

This script will:
- ✅ Create resource group
- ✅ Create storage account
- ✅ Create file share
- ✅ Create app service plan
- ✅ Create API app service
- ✅ Configure Azure File Storage
- ✅ Create static web app

## Step 3: Manual Deployment (Alternative)

If you prefer manual steps or need more control:

### 3.1 Set Variables

```bash
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"  # Or your preferred region
# Generate shorter storage account name (max 24 chars, lowercase + numbers only)
STORAGE_ACCOUNT="hf$(date +%s | tail -c 8)"  # Must be globally unique, 3-24 chars
AZURE_STORAGE_FILE_SHARE_NAME="healthforesight-data"
APP_SERVICE_PLAN="healthforesight-plan"
API_APP_NAME="healthforesight-api-$(date +%s)"  # Must be globally unique
WEB_APP_NAME="healthforesight-web-$(date +%s)"  # Must be globally unique
```

### 3.2 Create Resource Group

```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 3.3 Create Storage Account and File Share

```bash
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

### 3.4 Create App Service Plan

```bash
# Use B1 (Basic) for production, or F1 (Free) for development/testing
# Pay-As-You-Go subscriptions typically have quota for Basic/Standard tiers
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux

# Note: With Pay-As-You-Go subscription, you should have quota for:
# - B1/B2 (Basic) - Recommended for production (~$13-25/month)
# - S1+ (Standard) - For auto-scaling (~$55+/month)
# - F1 (Free) - For development/testing (has limitations)
```

### 3.5 Create API App Service

```bash
# Create API app
az webapp create \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11"

# Configure app settings
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
    LOG_LEVEL=INFO \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Configure startup command
az webapp config set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000"

# Enable Always On
az webapp config set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --always-on true
```

### 3.6 Deploy API Code

**Option A: Deploy from Local (ZIP)**

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/api"

# Create deployment ZIP
# Exclude unnecessary files
zip -r deploy.zip . \
  -x "*.git*" \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.log" \
  -x "*.pytest_cache*" \
  -x "*.mypy_cache*"

# Deploy to Azure
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src deploy.zip

# Clean up
rm deploy.zip
```

**Option B: Deploy from Git (Recommended)**

```bash
# Initialize git if not already
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
git init
git add .
git commit -m "Initial commit"

# Configure deployment from local git
az webapp deployment source config-local-git \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output tsv

# Get deployment URL
DEPLOYMENT_URL=$(az webapp deployment source show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query url -o tsv)

# Add remote and push
git remote add azure $DEPLOYMENT_URL
git push azure main
```

### 3.7 Create Static Web App for Frontend

```bash
# Create static web app
az staticwebapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Free

# Get API URL
API_URL=$(az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName -o tsv)

# Configure app settings
az staticwebapp appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting-names \
    VITE_API_URL="https://$API_URL/api/v1" \
    VITE_API_BASE_URL="https://$API_URL/api/v1"
```

### 3.8 Build and Deploy Web App

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to Static Web App
# Get deployment token
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.apiKey -o tsv)

# Deploy using SWA CLI (install: npm install -g @azure/static-web-apps-cli)
# Or use Azure Portal deployment
```

### 3.9 Configure CORS

```bash
# Get web app URL
WEB_URL=$(az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

# Add CORS origins
az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_URL"
```

## Step 4: Verify Deployment

```bash
# Check API health
API_URL=$(az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName -o tsv)

curl https://$API_URL/health

# Check API docs
echo "API Docs: https://$API_URL/docs"

# Get web app URL
WEB_URL=$(az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

echo "Web App: https://$WEB_URL"
```

## Step 5: View Logs

```bash
# Stream API logs
az webapp log tail \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file api-logs.zip
```

## Step 6: Update Deployment

After making code changes:

```bash
# For API - Redeploy
cd apps/api
zip -r deploy.zip . -x "*.git*" -x "*.venv*" -x "*__pycache__*"
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src deploy.zip
rm deploy.zip

# For Web - Rebuild and redeploy
cd apps/web
npm run build
# Deploy using SWA CLI or Azure Portal
```

## Troubleshooting

### API Not Starting

```bash
# Check logs
az webapp log tail --name $API_APP_NAME --resource-group $RESOURCE_GROUP

# Check app settings
az webapp config appsettings list \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Check if startup file is correct
az webapp config show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query linuxFxVersion
```

### File Storage Not Working

```bash
# Verify storage account
az storage account show \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP

# Check file share
az storage share list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY
```

### CORS Issues

```bash
# Add web app to CORS
WEB_URL=$(az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_URL"
```

## Next Steps

1. ✅ **Test the deployment** - Verify all endpoints work
2. ✅ **Set up monitoring** - Configure Azure Monitor
3. ✅ **Set up CI/CD** - GitHub Actions or Azure DevOps
4. ✅ **Configure custom domain** - Add your own domain
5. ✅ **Set up backups** - Configure Azure File Storage backups
6. ✅ **Optimize costs** - Review and optimize Azure costs

## Cost Management

### Estimated Monthly Costs

- **API App Service (B1)**: ~$13/month
- **Static Web App (Free)**: $0/month
- **Azure File Storage (100GB)**: ~$6/month
- **Total**: ~$20-30/month

### Cost Optimization Tips

1. Use Free tier for Static Web App
2. Scale down App Service when not in use
3. Monitor file storage usage
4. Use Azure Cost Management to track spending

## Summary

✅ **Simple Deployment**: Use Azure App Service
✅ **File Storage**: Azure File Storage configured
✅ **Auto-Scaling**: Built into App Service
✅ **Cost-Effective**: ~$20-30/month
✅ **Easy Management**: Azure Portal for everything

Your platform is ready to deploy to Azure!
