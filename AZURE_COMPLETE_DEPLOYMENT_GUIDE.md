# Complete Azure Deployment Guide - File-Based Solution

## Overview

This guide covers deploying the complete file-based HealthForesight platform to Azure, including:
- All data files (policies, analyses, baselines, observations, etc.)
- All configurations and metadata
- All execution data (pipeline runs, ingestions, etc.)
- Source data files (synthetic data)
- Target data model files

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Resources                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌──────────────────┐         │
│  │  App Service      │    │  Static Web Apps │         │
│  │  (API Backend)    │    │  (Frontend)      │         │
│  └────────┬─────────┘    └──────────────────┘         │
│           │                                              │
│           │                                              │
│  ┌────────▼──────────────────────────────────┐         │
│  │  Azure File Storage                        │         │
│  │  ┌────────────────────────────────────┐  │         │
│  │  │  File Share: healthforesight-data   │  │         │
│  │  │  ├── data/                          │  │         │
│  │  │  │   ├── policies/                  │  │         │
│  │  │  │   ├── analyses/                  │  │         │
│  │  │  │   ├── baselines/                 │  │         │
│  │  │  │   ├── observations/              │  │         │
│  │  │  │   ├── pipelines/                 │  │         │
│  │  │  │   ├── pipeline_runs/            │  │         │
│  │  │  │   └── ...                        │  │         │
│  │  │  ├── target_data_model/             │  │         │
│  │  │  └── source_data/                   │  │         │
│  │  └────────────────────────────────────┘  │         │
│  └──────────────────────────────────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed and logged in: `az login`
3. **Python 3.11+** (for migration scripts)
4. **Azure Storage File Share SDK**: `pip install azure-storage-file-share`

## Step 1: Create Azure Resources

### 1.1 Create Resource Group

```bash
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"  # Change to your preferred region

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 1.2 Create Storage Account

```bash
STORAGE_ACCOUNT="healthforesight$(date +%s | tail -c 6)"  # Unique name
FILE_SHARE_NAME="healthforesight-data"

# Create storage account
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2

# Create file share
az storage share create \
  --account-name $STORAGE_ACCOUNT \
  --name $FILE_SHARE_NAME \
  --quota 100  # 100 GB (adjust as needed)
```

### 1.3 Get Storage Account Key

```bash
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

echo "Storage Account: $STORAGE_ACCOUNT"
echo "Storage Key: $STORAGE_KEY"  # Save this securely!
```

## Step 2: Upload All Data to Azure File Storage

### 2.1 Use Automated Migration Script

```bash
# Run the migration script
./migrate-data-to-azure.sh
```

The script will:
- Upload all files from `apps/api/data/`
- Upload all files from `apps/api/data/target_data_model/`
- Upload source data from `data/source_data/`
- Verify uploads

### 2.2 Manual Upload (Alternative)

If you prefer manual control:

```bash
# Upload main data directory
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source apps/api/data \
  --destination $FILE_SHARE_NAME \
  --destination-path data

# Upload target data model
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source apps/api/data/target_data_model \
  --destination $FILE_SHARE_NAME \
  --destination-path target_data_model

# Upload source data (synthetic data)
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source data/source_data \
  --destination $FILE_SHARE_NAME \
  --destination-path source_data
```

### 2.3 Verify Uploads

```bash
# List all files in the share
az storage file list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --share-name $FILE_SHARE_NAME \
  --recursive \
  --output table

# Count files
az storage file list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --share-name $FILE_SHARE_NAME \
  --recursive \
  --query "[?type=='File'].name" -o tsv | wc -l
```

## Step 3: Create App Service for API

### 3.1 Create App Service Plan

```bash
APP_SERVICE_PLAN="healthforesight-plan"

az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1  # Basic tier (upgrade as needed)
```

### 3.2 Create Web App (API)

```bash
API_APP_NAME="healthforesight-api-$(date +%s | tail -c 6)"

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.11"
```

### 3.3 Configure App Settings

```bash
# Set Azure File Storage configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE_NAME \
    USE_FILE_STORAGE=true \
    STORAGE_PATH=/home/data \
    ENVIRONMENT=production \
    CORS_ORIGINS="https://$API_APP_NAME.azurewebsites.net,https://your-frontend-url.azurestaticapps.net"
```

### 3.4 Configure Startup Command

```bash
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "gunicorn uepi_api.main:app --bind 0.0.0.0:8000 --workers 2"
```

## Step 4: Deploy API Code

### 4.1 Option A: Deploy from Local Git

```bash
# Enable local git deployment
az webapp deployment source config-local-git \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME

# Get deployment URL
DEPLOYMENT_URL=$(az webapp deployment source show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query url -o tsv)

# Add remote and push
cd apps/api
git remote add azure $DEPLOYMENT_URL
git push azure main
```

### 4.2 Option B: Deploy from ZIP

```bash
# Create deployment package
cd apps/api
zip -r ../../api-deployment.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"

# Deploy
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src ../../api-deployment.zip
```

### 4.3 Option C: Deploy from GitHub

```bash
az webapp deployment source config \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --repo-url https://github.com/your-org/your-repo \
  --branch main \
  --manual-integration
```

## Step 5: Deploy Frontend

### 5.1 Build Frontend

```bash
cd apps/web
npm install
npm run build
```

### 5.2 Option A: Azure Static Web Apps

```bash
# Create Static Web App
STATIC_WEB_APP_NAME="healthforesight-web"

az staticwebapp create \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --source apps/web \
  --app-location "apps/web" \
  --output-location "dist" \
  --branch main

# Get the URL
az staticwebapp show \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv
```

### 5.3 Option B: App Service (Alternative)

```bash
WEB_APP_NAME="healthforesight-web-$(date +%s | tail -c 6)"

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime "NODE:18-lts"

# Deploy built files
cd apps/web/dist
zip -r ../../../web-deployment.zip .

az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src ../../../web-deployment.zip
```

## Step 6: Configure CORS and API URL

### 6.1 Update Frontend API URL

Update `apps/web/.env.production` or build-time environment variable:

```bash
VITE_API_URL=https://$API_APP_NAME.azurewebsites.net/api/v1
```

### 6.2 Update API CORS Settings

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    CORS_ORIGINS="https://$STATIC_WEB_APP_NAME.azurestaticapps.net,https://$WEB_APP_NAME.azurewebsites.net"
```

## Step 7: Mount Azure File Share (Optional but Recommended)

For better performance, you can mount the Azure File Share directly to the App Service:

```bash
# Get storage account connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --query connectionString -o tsv)

# Configure storage mount
az webapp config storage-account add \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --custom-id data \
  --storage-type AzureFiles \
  --share-name $FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT \
  --access-key $STORAGE_KEY \
  --mount-path /home/data
```

Then update app settings to use the mounted path:

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    STORAGE_PATH=/home/data \
    USE_AZURE_FILE_STORAGE=false  # Use mounted filesystem instead
```

## Step 8: Verify Deployment

### 8.1 Check API Health

```bash
# Get API URL
API_URL="https://$API_APP_NAME.azurewebsites.net"

# Test health endpoint
curl $API_URL/api/v1/health

# Test policies endpoint
curl $API_URL/api/v1/policies \
  -H "Authorization: Bearer demo-token"
```

### 8.2 Check Logs

```bash
# Stream logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME

# Download logs
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --log-file api-logs.zip
```

### 8.3 Verify Data Access

```bash
# List files in Azure File Share from API
curl $API_URL/api/v1/policies \
  -H "Authorization: Bearer demo-token" | jq 'length'

# Should return the number of policies from your local system
```

## Step 9: Set Up Continuous Deployment (Optional)

### 9.1 GitHub Actions

Create `.github/workflows/azure-deploy.yml`:

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
          app-name: ${{ secrets.AZURE_WEBAPP_NAME }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: ./apps/api

  deploy-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd apps/web
          npm install
          npm run build
      - uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "apps/web"
          output_location: "dist"
```

## Step 10: Backup and Maintenance

### 10.1 Create Backup Script

```bash
#!/bin/bash
# backup-azure-data.sh

STORAGE_ACCOUNT="your-storage-account"
STORAGE_KEY="your-storage-key"
FILE_SHARE_NAME="healthforesight-data"
BACKUP_CONTAINER="backups"

# Create backup container
az storage container create \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name $BACKUP_CONTAINER

# Create snapshot of file share
az storage share snapshot create \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --share-name $FILE_SHARE_NAME \
  --name "backup-$(date +%Y%m%d-%H%M%S)"
```

### 10.2 Schedule Backups

Use Azure Automation or Logic Apps to schedule regular backups.

## Troubleshooting

### Issue: Files not accessible

**Solution**: Check file permissions and mount path:
```bash
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME
```

### Issue: API not starting

**Solution**: Check logs:
```bash
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME
```

### Issue: CORS errors

**Solution**: Update CORS_ORIGINS in app settings with exact frontend URL.

## Cost Estimation

- **Storage Account (Standard LRS)**: ~$0.06/GB/month
- **App Service Plan (B1)**: ~$13/month
- **Static Web Apps**: Free tier available
- **Total (estimated)**: ~$15-30/month for small-medium workloads

## Next Steps

1. ✅ Set up monitoring and alerts
2. ✅ Configure custom domain
3. ✅ Set up SSL certificates
4. ✅ Configure auto-scaling
5. ✅ Set up backup automation
6. ✅ Configure Application Insights

## Summary

After completing these steps, you'll have:
- ✅ All data files in Azure File Storage
- ✅ API running on Azure App Service
- ✅ Frontend deployed to Azure Static Web Apps
- ✅ Complete file-based solution running in Azure
- ✅ All configurations and metadata preserved

Your Azure deployment will be identical to your local system!


