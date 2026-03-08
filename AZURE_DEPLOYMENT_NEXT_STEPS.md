# Azure Deployment - Next Steps

## ✅ Migration Complete!

Your Azure resources have been created successfully:

- **Resource Group**: `healthforesight-rg`
- **Storage Account**: `healthforesight9016`
- **File Share**: `healthforesight-data`
- **API App**: `healthforesight-api-9016`
- **Static Web App**: `healthforesight-web-9016`

## 🚀 Deploy Your Code

### Option 1: Deploy Everything at Once (Recommended)

```bash
# Set the resource names
export RESOURCE_GROUP="healthforesight-rg"
export API_APP_NAME="healthforesight-api-9016"
export STATIC_WEB_APP_NAME="healthforesight-web-9016"

# Run the complete deployment script
./scripts/azure/deploy-complete.sh
```

### Option 2: Deploy Separately

#### Step 1: Deploy API

```bash
export RESOURCE_GROUP="healthforesight-rg"
export API_APP_NAME="healthforesight-api-9016"

./scripts/azure/deploy-api.sh
```

#### Step 2: Deploy Frontend

```bash
export RESOURCE_GROUP="healthforesight-rg"
export STATIC_WEB_APP_NAME="healthforesight-web-9016"
export API_URL="https://healthforesight-api-9016.azurewebsites.net"

./scripts/azure/deploy-frontend.sh
```

## 🔍 Verify Deployment

### Test API

```bash
# Test health endpoint
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/health

# View API docs
open https://healthforesight-api-9016.azurewebsites.net/docs
```

### Check Logs

```bash
# View API logs
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

### Verify File Storage

```bash
# List files in Azure File Share
az storage file list \
  --account-name healthforesight9016 \
  --share-name healthforesight-data \
  --path data \
  --account-key $(az storage account keys list \
    --resource-group healthforesight-rg \
    --account-name healthforesight9016 \
    --query "[0].value" -o tsv)
```

## 📝 Important URLs

- **API**: https://healthforesight-api-9016.azurewebsites.net
- **API Docs**: https://healthforesight-api-9016.azurewebsites.net/docs
- **Frontend**: Check Azure Portal for Static Web App URL

## ⚙️ Configuration

The API is configured with:
- ✅ Azure File Storage enabled
- ✅ Storage account: `healthforesight9016`
- ✅ File share: `healthforesight-data`
- ✅ Environment: `production`

## 🐛 Troubleshooting

### API Not Starting

```bash
# Check logs
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016

# Check app settings
az webapp config appsettings list \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

### Frontend Can't Connect to API

1. Verify API URL in frontend `.env.production`
2. Check CORS settings in API
3. Verify API is running

### Data Not Accessible

```bash
# Verify file share exists
az storage share list \
  --account-name healthforesight9016 \
  --account-key $(az storage account keys list \
    --resource-group healthforesight-rg \
    --account-name healthforesight9016 \
    --query "[0].value" -o tsv)
```

## 🎯 Next Steps After Deployment

1. ✅ **Test all endpoints** - Verify API functionality
2. ✅ **Test frontend** - Verify UI works with Azure API
3. ✅ **Set up custom domain** (optional)
4. ✅ **Configure CI/CD** - GitHub Actions or Azure DevOps
5. ✅ **Set up monitoring** - Azure Monitor and Application Insights
6. ✅ **Configure backups** - Azure File Storage snapshots

## 📊 Quick Commands

```bash
# Get API URL
API_URL=$(az webapp show \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query defaultHostName -o tsv)
echo "API URL: https://$API_URL"

# Get Static Web App URL
WEB_URL=$(az staticwebapp show \
  --name healthforesight-web-9016 \
  --resource-group healthforesight-rg \
  --query defaultHostname -o tsv)
echo "Frontend URL: https://$WEB_URL"
```

Ready to deploy? Run:
```bash
./scripts/azure/deploy-complete.sh
```

