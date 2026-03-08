# Azure Migration - Quick Start Guide

## 🚀 Ready to Migrate to Azure!

Your Azure quota is settled. Follow these steps to migrate your platform to Azure.

## Prerequisites Check

```bash
# 1. Check Azure CLI
az --version

# 2. Login to Azure
az login

# 3. Set subscription (if you have multiple)
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## Quick Migration (Automated)

### Option 1: Use the Complete Migration Script

```bash
# Run the automated migration script
./scripts/azure/migrate-to-azure.sh
```

This script will:
- ✅ Create all Azure resources
- ✅ Set up Azure File Storage
- ✅ Migrate your local data
- ✅ Configure environment variables
- ✅ Deploy API and Frontend

### Option 2: Step-by-Step Manual Migration

#### Step 1: Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="healthforesight$(date +%s | tail -c 5)"
FILE_SHARE="healthforesight-data"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --sku Standard_LRS

# Create file share
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

az storage share create \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE \
  --quota 100
```

#### Step 2: Migrate Data

```bash
# Upload local data to Azure File Share
CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --query connectionString -o tsv)

az storage file upload-batch \
  --connection-string "$CONNECTION_STRING" \
  --source ./data \
  --destination $FILE_SHARE \
  --destination-path data
```

#### Step 3: Deploy API

```bash
# Create App Service
API_APP="healthforesight-api-$(date +%s | tail -c 5)"
APP_PLAN="healthforesight-plan"

az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --name $API_APP \
  --runtime "PYTHON:3.11"

# Configure settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE \
    USE_FILE_STORAGE=true \
    ENVIRONMENT=production

# Deploy code
./scripts/azure/deploy-api.sh
```

#### Step 4: Deploy Frontend

```bash
# Create Static Web App
STATIC_WEB="healthforesight-web-$(date +%s | tail -c 5)"

az staticwebapp create \
  --name $STATIC_WEB \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Free

# Deploy frontend
API_URL="https://$API_APP.azurewebsites.net"
export API_URL
./scripts/azure/deploy-frontend.sh
```

#### Step 5: Verify

```bash
# Run verification script
./scripts/azure/verify-deployment.sh
```

## Configuration Summary

After migration, your Azure resources will have:

### Storage Account
- **Type**: Standard_LRS
- **File Share**: `healthforesight-data`
- **Mount Path**: `/home/data` (in App Service)

### App Service (API)
- **Runtime**: Python 3.11
- **Plan**: Basic B1
- **Environment Variables**:
  - `USE_AZURE_FILE_STORAGE=true`
  - `AZURE_STORAGE_ACCOUNT_NAME=<your-storage>`
  - `AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data`

### Static Web App (Frontend)
- **Tier**: Free
- **Build**: Automatic from GitHub (or manual deploy)

## Testing After Migration

```bash
# 1. Test API health
curl https://$API_APP.azurewebsites.net/api/v1/health

# 2. Test API docs
open https://$API_APP.azurewebsites.net/docs

# 3. Check logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP

# 4. Verify file storage
az storage share list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY
```

## Troubleshooting

### API Not Starting
```bash
# Check logs
az webapp log tail --name $API_APP --resource-group $RESOURCE_GROUP

# Check app settings
az webapp config appsettings list \
  --name $API_APP \
  --resource-group $RESOURCE_GROUP
```

### Data Not Accessible
```bash
# Verify file share exists
az storage share list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

# Check mounted storage
az webapp config storage-account list \
  --name $API_APP \
  --resource-group $RESOURCE_GROUP
```

### Frontend Can't Connect
1. Update `VITE_API_URL` in frontend build
2. Check CORS settings in API
3. Verify API URL is correct

## Cost Estimate

- **App Service (B1)**: ~$13/month
- **Static Web App (Free)**: $0/month
- **File Storage (100GB)**: ~$6/month
- **Total**: ~$20/month

## Next Steps

1. ✅ **Set up CI/CD** - GitHub Actions or Azure DevOps
2. ✅ **Configure custom domain** - Add your own domain
3. ✅ **Set up monitoring** - Azure Monitor and Application Insights
4. ✅ **Configure backups** - Azure File Storage snapshots
5. ✅ **Set up staging environment** - Separate resource group

## Resources

- **Complete Guide**: `AZURE_MIGRATION_COMPLETE.md`
- **Deployment Scripts**: `scripts/azure/`
- **Azure File Storage**: Already implemented in codebase

## Ready to Start?

Run the migration script:

```bash
./scripts/azure/migrate-to-azure.sh
```

Or follow the step-by-step guide in `AZURE_MIGRATION_COMPLETE.md`.

Good luck with your Azure migration! 🚀

