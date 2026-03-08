# Azure Deployment - Quick Start Guide

## 🚀 Quick Deployment

The easiest way to deploy to Azure is using the automated script:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./DEPLOY_TO_AZURE.sh
```

This script will guide you through the entire deployment process.

## Prerequisites

1. **Azure Account** - Sign up at https://azure.microsoft.com/free/
2. **Azure CLI** - Install:
   ```bash
   # macOS
   brew install azure-cli
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```
3. **Login to Azure**:
   ```bash
   az login
   ```

## What Gets Deployed

### Infrastructure
- ✅ **Resource Group** - Container for all resources
- ✅ **Storage Account** - For Azure File Storage
- ✅ **File Share** - For storing platform data
- ✅ **App Service Plan** - For hosting API
- ✅ **API App Service** - FastAPI backend
- ✅ **Static Web App** - React frontend

### Configuration
- ✅ **Azure File Storage** - Configured automatically
- ✅ **Environment Variables** - Set automatically
- ✅ **CORS** - Configured between web and API
- ✅ **Startup Command** - Configured for FastAPI

## Deployment Steps (Automated)

The `DEPLOY_TO_AZURE.sh` script handles:

1. ✅ Checks prerequisites
2. ✅ Prompts for configuration
3. ✅ Creates all Azure resources
4. ✅ Configures Azure File Storage
5. ✅ Deploys API code
6. ✅ Configures web app
7. ✅ Sets up CORS

## Manual Deployment

If you prefer manual steps, see:
- **Detailed Guide**: `AZURE_DEPLOYMENT_STEP_BY_STEP.md`
- **Complete Guide**: `AZURE_DEPLOYMENT_GUIDE.md`

## Post-Deployment

### 1. Test API

```bash
# Get API URL
API_URL=$(az webapp show \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --query defaultHostName -o tsv)

# Test health endpoint
curl https://$API_URL/health

# View API docs
open https://$API_URL/docs
```

### 2. Deploy Web App

After the script completes, deploy the web app:

```bash
cd apps/web

# Install SWA CLI (if not installed)
npm install -g @azure/static-web-apps-cli

# Deploy (use token from script output)
swa deploy ./dist \
  --deployment-token <your-deployment-token> \
  --env production
```

Or use Azure Portal:
1. Go to Azure Portal
2. Navigate to Static Web Apps > Your Web App
3. Click "Browse" to open your app

### 3. Verify Everything Works

```bash
# Check API logs
az webapp log tail \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg

# Check file storage
az storage share list \
  --account-name <your-storage-account> \
  --account-key <your-storage-key>
```

## Configuration

The script automatically configures:

### API App Settings
```bash
USE_AZURE_FILE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
AZURE_STORAGE_ACCOUNT_KEY=<storage-key>
AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data
USE_FILE_STORAGE=true
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Web App Settings
```bash
VITE_API_URL=https://<api-app-name>.azurewebsites.net/api/v1
VITE_API_BASE_URL=https://<api-app-name>.azurewebsites.net/api/v1
```

## Cost Estimation

### Monthly Costs (Approximate)
- **API App Service (B1)**: ~$13/month
- **Static Web App (Free)**: $0/month
- **Azure File Storage (100GB)**: ~$6/month
- **Total**: ~$20-30/month

### Cost Optimization
- Use Free tier for Static Web Apps
- Use Basic (B1) tier for App Service
- Monitor storage usage
- Scale down when not in use

## Troubleshooting

### API Not Starting

```bash
# View logs
az webapp log tail \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg

# Check app settings
az webapp config appsettings list \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg
```

### File Storage Not Working

```bash
# Verify storage account
az storage account show \
  --name <your-storage-account> \
  --resource-group healthforesight-rg

# Check file share
az storage share list \
  --account-name <your-storage-account> \
  --account-key <your-storage-key>
```

### CORS Issues

```bash
# Get web app URL
WEB_URL=$(az staticwebapp show \
  --name <your-web-app-name> \
  --resource-group healthforesight-rg \
  --query defaultHostname -o tsv)

# Add to CORS
az webapp cors add \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --allowed-origins "https://$WEB_URL"
```

## Next Steps

1. ✅ **Test the deployment** - Verify all endpoints work
2. ✅ **Set up CI/CD** - GitHub Actions or Azure DevOps
3. ✅ **Configure custom domain** - Add your own domain
4. ✅ **Set up monitoring** - Azure Monitor alerts
5. ✅ **Configure backups** - Azure File Storage backups

## Resources

- **Deployment Guide**: `AZURE_DEPLOYMENT_STEP_BY_STEP.md`
- **Complete Guide**: `AZURE_DEPLOYMENT_GUIDE.md`
- **Deployment Summary**: `AZURE_DEPLOYMENT_SUMMARY.md`
- **File Storage Setup**: `AZURE_FILE_STORAGE_SETUP.md`

## Summary

✅ **Simple**: One script deploys everything
✅ **Automated**: No manual configuration needed
✅ **File-Based**: Uses Azure File Storage
✅ **Cost-Effective**: ~$20-30/month
✅ **Scalable**: Auto-scaling built-in

Run `./DEPLOY_TO_AZURE.sh` to get started!
