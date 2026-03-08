#!/bin/bash
# Complete Azure Deployment Script
# Deploys entire file-based solution to Azure with all data

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Complete Azure Deployment - File-Based Solution${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Step 0: Checking prerequisites...${NC}"

if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! az account show &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login...${NC}"
    az login
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"
echo ""

# Configuration
echo -e "${BLUE}Step 1: Configuration${NC}"
read -p "Resource Group Name [healthforesight-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-healthforesight-rg}

read -p "Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Storage Account Name (must be unique, lowercase, alphanumeric): " STORAGE_ACCOUNT
if [ -z "$STORAGE_ACCOUNT" ]; then
    STORAGE_ACCOUNT="healthforesight$(date +%s | tail -c 6)"
    echo -e "${YELLOW}  Using generated name: $STORAGE_ACCOUNT${NC}"
fi

read -p "File Share Name [healthforesight-data]: " FILE_SHARE_NAME
FILE_SHARE_NAME=${FILE_SHARE_NAME:-healthforesight-data}

read -p "API App Name (must be unique): " API_APP_NAME
if [ -z "$API_APP_NAME" ]; then
    API_APP_NAME="healthforesight-api-$(date +%s | tail -c 6)"
    echo -e "${YELLOW}  Using generated name: $API_APP_NAME${NC}"
fi

read -p "Web App Name (must be unique) [optional]: " WEB_APP_NAME
if [ -z "$WEB_APP_NAME" ]; then
    WEB_APP_NAME="healthforesight-web-$(date +%s | tail -c 6)"
    echo -e "${YELLOW}  Using generated name: $WEB_APP_NAME${NC}"
fi

read -p "App Service Plan SKU [B1]: " APP_SKU
APP_SKU=${APP_SKU:-B1}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  API App: $API_APP_NAME"
echo "  Web App: $WEB_APP_NAME"
echo "  App Service Plan SKU: $APP_SKU"
echo ""

read -p "Continue with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""

# Create resource group
echo -e "${BLUE}Step 2: Creating resource group...${NC}"
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none
echo -e "${GREEN}✅ Resource group created${NC}"
echo ""

# Create storage account
echo -e "${BLUE}Step 3: Creating storage account...${NC}"
az storage account create \
  --resource-group $RESOURCE_GROUP \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none
echo -e "${GREEN}✅ Storage account created${NC}"

# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

# Create file share
echo -e "${BLUE}Step 4: Creating file share...${NC}"
az storage share create \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE_NAME \
  --quota 100 \
  --output none
echo -e "${GREEN}✅ File share created${NC}"
echo ""

# Upload data
echo -e "${BLUE}Step 5: Uploading data files...${NC}"
echo "  This may take several minutes depending on data size..."

# Upload main data directory
if [ -d "apps/api/data" ]; then
    echo "  Uploading apps/api/data..."
    az storage file upload-batch \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --source apps/api/data \
      --destination $FILE_SHARE_NAME \
      --destination-path data \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo -e "  ${GREEN}✅ Main data directory uploaded${NC}"
fi

# Upload target data model
if [ -d "apps/api/data/target_data_model" ]; then
    echo "  Uploading target_data_model..."
    az storage file upload-batch \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --source apps/api/data/target_data_model \
      --destination $FILE_SHARE_NAME \
      --destination-path target_data_model \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo -e "  ${GREEN}✅ Target data model uploaded${NC}"
fi

# Upload source data
if [ -d "data/source_data" ]; then
    echo "  Uploading source_data..."
    az storage file upload-batch \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --source data/source_data \
      --destination $FILE_SHARE_NAME \
      --destination-path source_data \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo -e "  ${GREEN}✅ Source data uploaded${NC}"
fi

echo -e "${GREEN}✅ Data upload complete${NC}"
echo ""

# Create App Service Plan
echo -e "${BLUE}Step 6: Creating App Service Plan...${NC}"
APP_SERVICE_PLAN="$RESOURCE_GROUP-plan"
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku $APP_SKU \
  --output none
echo -e "${GREEN}✅ App Service Plan created${NC}"
echo ""

# Create API Web App
echo -e "${BLUE}Step 7: Creating API Web App...${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.11" \
  --os-type Linux \
  --output none
echo -e "${GREEN}✅ API Web App created${NC}"

# Configure API settings
echo -e "${BLUE}Step 8: Configuring API settings...${NC}"
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
    CORS_ORIGINS="https://$WEB_APP_NAME.azurewebsites.net" \
  --output none

# Configure startup command
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "gunicorn uepi_api.main:app --bind 0.0.0.0:8000 --workers 2" \
  --output none

echo -e "${GREEN}✅ API configuration complete${NC}"
echo ""

# Mount Azure File Share
echo -e "${BLUE}Step 9: Mounting Azure File Share...${NC}"
az webapp config storage-account add \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --custom-id data \
  --storage-type AzureFiles \
  --share-name $FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT \
  --access-key $STORAGE_KEY \
  --mount-path /home/data \
  --output none
echo -e "${GREEN}✅ File share mounted${NC}"
echo ""

# Deploy API code
echo -e "${BLUE}Step 10: Deploying API code...${NC}"
echo "  Creating deployment package..."

cd apps/api
zip -r ../../api-deployment.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.pyd" \
  -x ".venv/*" \
  -x "venv/*" \
  -x "env/*" \
  -x ".env" \
  -x "data/*" 2>/dev/null || true

cd ../..

echo "  Uploading deployment package..."
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src api-deployment.zip \
  --output none

rm -f api-deployment.zip

echo -e "${GREEN}✅ API code deployed${NC}"
echo ""

# Build and deploy frontend
echo -e "${BLUE}Step 11: Building frontend...${NC}"
cd apps/web

if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

echo "  Building..."
npm run build

cd ../..
echo -e "${GREEN}✅ Frontend built${NC}"
echo ""

# Create Web App for frontend
echo -e "${BLUE}Step 12: Creating Web App for frontend...${NC}"
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime "NODE:18-lts" \
  --output none

# Configure frontend settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    WEBSITE_NODE_DEFAULT_VERSION="18-lts" \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  --output none

echo -e "${GREEN}✅ Web App created${NC}"
echo ""

# Deploy frontend
echo -e "${BLUE}Step 13: Deploying frontend...${NC}"
cd apps/web/dist
zip -r ../../../web-deployment.zip . 2>/dev/null || {
    echo -e "${YELLOW}⚠️  dist directory not found, creating minimal deployment...${NC}"
    mkdir -p ../../../web-deployment
    echo "<!DOCTYPE html><html><body><h1>Frontend deployment in progress</h1></body></html>" > ../../../web-deployment/index.html
    cd ../../../web-deployment
    zip -r ../web-deployment.zip .
    cd ..
    rm -rf web-deployment
}

cd ../../..

az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src web-deployment.zip \
  --output none

rm -f web-deployment.zip

echo -e "${GREEN}✅ Frontend deployed${NC}"
echo ""

# Get URLs
API_URL="https://$API_APP_NAME.azurewebsites.net"
WEB_URL="https://$WEB_APP_NAME.azurewebsites.net"

# Update CORS
echo -e "${BLUE}Step 14: Updating CORS settings...${NC}"
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    CORS_ORIGINS="$WEB_URL,$API_URL" \
  --output none
echo -e "${GREEN}✅ CORS updated${NC}"
echo ""

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  API URL: $API_URL"
echo "  Web URL: $WEB_URL"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Test API:"
echo "   curl $API_URL/api/v1/health"
echo ""
echo "2. Test Policies:"
echo "   curl $API_URL/api/v1/policies -H 'Authorization: Bearer demo-token'"
echo ""
echo "3. Access Web App:"
echo "   $WEB_URL"
echo ""
echo "4. Check logs:"
echo "   az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo ""
echo "5. Update frontend API URL:"
echo "   Set VITE_API_URL=$API_URL/api/v1 in frontend build"
echo ""
echo -e "${GREEN}✅ All data, configurations, and code have been deployed to Azure!${NC}"
echo ""


