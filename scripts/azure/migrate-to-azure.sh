#!/bin/bash
# Complete Azure Migration Script
# This script automates the entire migration process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
LOCATION="${LOCATION:-eastus}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-healthforesight$(date +%s | tail -c 5)}"
FILE_SHARE_NAME="${FILE_SHARE_NAME:-healthforesight-data}"
APP_SERVICE_PLAN="${APP_SERVICE_PLAN:-healthforesight-plan}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-$(date +%s | tail -c 5)}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web-$(date +%s | tail -c 5)}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Azure Migration Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Azure. Logging in...${NC}"
    az login
fi

echo -e "${GREEN}Step 1: Creating Resource Group${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

echo -e "${GREEN}Step 2: Creating Storage Account${NC}"
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT_NAME \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none

echo -e "${GREEN}Step 3: Creating File Share${NC}"
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query "[0].value" -o tsv)

az storage share create \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE_NAME \
  --quota 100 \
  --output none

echo -e "${GREEN}Step 4: Creating App Service Plan (Linux)${NC}"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux \
  --output none

echo -e "${GREEN}Step 5: Creating App Service (API) - Linux${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.11" \
  --output none

echo -e "${GREEN}Step 6: Configuring App Service Settings${NC}"
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME \
    AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE_NAME \
    AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
    ENVIRONMENT=production \
    USE_FILE_STORAGE=true \
    CORS_ORIGINS="https://$API_APP_NAME.azurewebsites.net" \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  --output none

# Configure startup command for Linux Python app
echo -e "${GREEN}Configuring startup command...${NC}"
# Set PYTHONPATH and use gunicorn
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot" \
  --output none

az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --chdir /home/site/wwwroot/src uepi_api.main:app" \
  --output none

echo -e "${GREEN}Step 7: Migrating Data to Azure File Storage${NC}"
if [ -d "./data" ]; then
    CONNECTION_STRING=$(az storage account show-connection-string \
      --resource-group $RESOURCE_GROUP \
      --name $STORAGE_ACCOUNT_NAME \
      --query connectionString -o tsv)
    
    echo "Uploading data files..."
    az storage file upload-batch \
      --connection-string "$CONNECTION_STRING" \
      --source ./data \
      --destination $FILE_SHARE_NAME \
      --destination-path data \
      --output none
    
    echo -e "${GREEN}Data migration completed${NC}"
else
    echo -e "${YELLOW}Warning: ./data directory not found. Skipping data migration.${NC}"
fi

echo -e "${GREEN}Step 8: Creating Static Web App${NC}"
# Static Web Apps are only available in specific regions
# Use eastus2 if eastus was selected, otherwise use the location
STATIC_WEB_LOCATION=$LOCATION
if [ "$LOCATION" = "eastus" ]; then
    STATIC_WEB_LOCATION="eastus2"
    echo -e "${YELLOW}Note: Static Web Apps not available in eastus, using eastus2${NC}"
fi

az staticwebapp create \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $STATIC_WEB_LOCATION \
  --sku Free \
  --output none

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "File Share: $FILE_SHARE_NAME"
echo "API App: https://$API_APP_NAME.azurewebsites.net"
echo "Static Web App: $STATIC_WEB_APP_NAME"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy API code: ./scripts/azure/deploy-api.sh"
echo "2. Deploy Frontend: ./scripts/azure/deploy-frontend.sh"
echo "3. Update frontend API URL to: https://$API_APP_NAME.azurewebsites.net"
echo ""
echo -e "${GREEN}Migration completed successfully!${NC}"

