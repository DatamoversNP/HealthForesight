#!/bin/bash

# Azure App Service Deployment Script
# Simple deployment for HealthForesight platform

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Azure App Service Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
LOCATION="${LOCATION:-eastus}"
APP_SERVICE_PLAN="${APP_SERVICE_PLAN:-healthforesight-plan}"
generate_api_name() {
    TIMESTAMP=$(date +%s | tail -c 8)
    echo "hf-api${TIMESTAMP}"
}
API_APP_NAME="${API_APP_NAME:-$(generate_api_name)}"
generate_web_name() {
    TIMESTAMP=$(date +%s | tail -c 8)
    echo "hf-web${TIMESTAMP}"
}
WEB_APP_NAME="${WEB_APP_NAME:-$(generate_web_name)}"
# Generate shorter storage account name (max 24 chars, lowercase + numbers only)
generate_storage_name() {
    TIMESTAMP=$(date +%s | tail -c 8)
    echo "hf${TIMESTAMP}" | head -c 24
}
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-$(generate_storage_name)}"
AZURE_STORAGE_FILE_SHARE_NAME="${AZURE_STORAGE_FILE_SHARE_NAME:-healthforesight-data}"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  API App: $API_APP_NAME"
echo "  Web App: $WEB_APP_NAME"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo ""

# Check if logged in
if ! az account show &>/dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
fi

# Create resource group
echo -e "${BLUE}Creating resource group...${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

# Create storage account
echo -e "${BLUE}Creating storage account...${NC}"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none

# Create file share
echo -e "${BLUE}Creating file share...${NC}"
az storage share create \
  --name $AZURE_STORAGE_FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT \
  --output none

# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

# Create app service plan (use F1 Free tier to avoid quota issues)
echo -e "${BLUE}Creating app service plan...${NC}"
APP_SERVICE_SKU="${APP_SERVICE_SKU:-F1}"  # Default to Free tier

# Try to create with specified SKU, fallback to F1 if quota error
if ! az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku $APP_SERVICE_SKU \
  --is-linux \
  --output none 2>&1 | grep -q "quota\|Quota"; then
    
    echo -e "${YELLOW}Quota error with $APP_SERVICE_SKU tier. Trying Free (F1) tier...${NC}"
    APP_SERVICE_SKU="F1"
    az appservice plan create \
      --name $APP_SERVICE_PLAN \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku F1 \
      --is-linux \
      --output none || {
        echo -e "${RED}Failed to create app service plan.${NC}"
        echo "Try: 1) Different location, 2) Request quota increase, or 3) Upgrade subscription"
        exit 1
    }
fi

# Create API app service
echo -e "${BLUE}Creating API app service...${NC}"
az webapp create \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11" \
  --output none

# Configure API app settings
echo -e "${BLUE}Configuring API app settings...${NC}"
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
  --output none

# Configure startup command
az webapp config set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000" \
  --output none

# Create static web app
echo -e "${BLUE}Creating static web app...${NC}"
az staticwebapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Free \
  --output none

# Get API URL
API_URL=$(az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName -o tsv)

# Configure web app settings
echo -e "${BLUE}Configuring web app settings...${NC}"
az staticwebapp appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting-names \
    VITE_API_URL=https://$API_URL \
    VITE_API_BASE_URL=https://$API_URL/api/v1 \
  --output none

# Configure CORS
echo -e "${BLUE}Configuring CORS...${NC}"
WEB_URL=$(az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_URL" \
  --output none

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}Resources created:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $AZURE_STORAGE_FILE_SHARE_NAME"
echo "  API App: $API_APP_NAME"
echo "  API URL: https://$API_URL"
echo "  Web App: $WEB_APP_NAME"
echo "  Web URL: https://$WEB_URL"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Deploy API code: cd apps/api && ./deploy-to-azure.sh"
echo "  2. Deploy Web code: cd apps/web && ./deploy-to-azure.sh"
echo "  3. Test deployment: curl https://$API_URL/health"
echo ""
