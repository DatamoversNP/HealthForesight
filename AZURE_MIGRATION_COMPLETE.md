# Complete Azure Migration Guide

## Overview

This guide provides a step-by-step process to migrate the HealthForesight platform from local development to Azure production.

## Prerequisites

1. **Azure Account** with quota settled ✅
2. **Azure CLI** installed and logged in
3. **Local data** ready for migration
4. **Environment variables** configured

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Resources                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌──────────────────┐         │
│  │  Static Web Apps │    │  App Service      │         │
│  │  (Frontend)      │───▶│  (API Backend)    │         │
│  └──────────────────┘    └────────┬─────────┘         │
│                                    │                    │
│                                    ▼                    │
│                          ┌──────────────────┐         │
│                          │ Azure File Storage│         │
│                          │  File Share       │         │
│                          └──────────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Step 1: Install and Configure Azure CLI

```bash
# Install Azure CLI (if not already installed)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set your subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify
az account show
```

## Step 2: Create Azure Resources

### 2.1 Create Resource Group

```bash
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"  # or your preferred region

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 2.2 Create Storage Account and File Share

```bash
STORAGE_ACCOUNT_NAME="healthforesight$(date +%s | tail -c 5)"  # Must be globally unique
FILE_SHARE_NAME="healthforesight-data"

# Create storage account
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT_NAME \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query "[0].value" -o tsv)

# Create file share
az storage share create \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE_NAME \
  --quota 100  # 100 GB
```

### 2.3 Create App Service Plan

```bash
APP_SERVICE_PLAN="healthforesight-plan"

az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1  # Basic tier (can upgrade later)
```

### 2.4 Create App Service (API)

```bash
API_APP_NAME="healthforesight-api-$(date +%s | tail -c 5)"  # Must be globally unique

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.11"
```

## Step 3: Configure Environment Variables

```bash
# Set Azure File Storage configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME \
    AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE_NAME \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    ENVIRONMENT=production \
    CORS_ORIGINS="https://$API_APP_NAME.azurewebsites.net"
```

## Step 4: Migrate Data to Azure

### 4.1 Install Azure File Share Tools

```bash
# Install azcopy (for efficient data transfer)
# macOS
brew install azcopy

# Linux
wget https://aka.ms/downloadazcopy-v10-linux
tar -xvf downloadazcopy-v10-linux
sudo mv azcopy_linux_amd64_*/azcopy /usr/local/bin/
```

### 4.2 Upload Data

```bash
# Get connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT_NAME \
  --query connectionString -o tsv)

# Upload local data directory to Azure File Share
az storage file upload-batch \
  --connection-string "$CONNECTION_STRING" \
  --source ./data \
  --destination $FILE_SHARE_NAME \
  --destination-path data
```

## Step 5: Deploy API to App Service

### 5.1 Prepare Deployment

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Create deployment package
zip -r ../api-deployment.zip . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x "*.git*" \
  -x "*.env*"
```

### 5.2 Deploy

```bash
# Deploy using Azure CLI
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src ../api-deployment.zip
```

## Step 6: Deploy Frontend to Static Web Apps

### 6.1 Create Static Web App

```bash
STATIC_WEB_APP_NAME="healthforesight-web-$(date +%s | tail -c 5)"

az staticwebapp create \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Free
```

### 6.2 Build and Deploy Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to Static Web Apps
az staticwebapp deploy \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --app-location "./" \
  --output-location "dist"
```

## Step 7: Update Frontend API Endpoint

After deployment, update the frontend to point to the Azure API:

```bash
# Get API URL
API_URL="https://$API_APP_NAME.azurewebsites.net"

# Update frontend environment
cd apps/web
echo "VITE_API_URL=$API_URL" > .env.production
```

## Step 8: Verify Deployment

### 8.1 Check API Health

```bash
curl https://$API_APP_NAME.azurewebsites.net/api/v1/health
```

### 8.2 Check App Service Logs

```bash
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME
```

### 8.3 Test Frontend

Visit: `https://$STATIC_WEB_APP_NAME.azurestaticapps.net`

## Step 9: Configure Custom Domain (Optional)

```bash
# Add custom domain to App Service
az webapp config hostname add \
  --webapp-name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname api.yourdomain.com
```

## Troubleshooting

### API Not Starting

1. Check logs: `az webapp log tail --name $API_APP_NAME`
2. Verify environment variables
3. Check Python version compatibility

### Data Not Accessible

1. Verify file share exists: `az storage share list --account-name $STORAGE_ACCOUNT_NAME`
2. Check permissions on storage account
3. Verify connection string is correct

### Frontend Can't Connect to API

1. Update CORS settings in API
2. Verify API URL in frontend environment
3. Check network tab in browser console

## Cost Optimization

- **Storage**: Use Standard_LRS (cheapest) for file storage
- **App Service**: Start with B1 (Basic), scale up as needed
- **Static Web Apps**: Free tier available
- **Monitor**: Use Azure Cost Management to track spending

## Next Steps

1. Set up CI/CD pipelines
2. Configure monitoring and alerts
3. Set up backup strategy
4. Configure SSL certificates
5. Set up staging environment

## Quick Reference

```bash
# Resource names (save these)
RESOURCE_GROUP="healthforesight-rg"
STORAGE_ACCOUNT_NAME="your-storage-account"
API_APP_NAME="your-api-app"
STATIC_WEB_APP_NAME="your-static-web-app"
FILE_SHARE_NAME="healthforesight-data"
```

