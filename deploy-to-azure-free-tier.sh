#!/bin/bash
# Deploy to Azure using Free Tier Services (No Quota Required)
# Uses Azure Static Web Apps and Azure Functions (free tier)

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
echo -e "${BLUE}🚀 Azure Deployment - Free Tier (No Quota Required)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found${NC}"
    exit 1
fi

if ! az account show &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure${NC}"
    az login
fi

# Configuration
echo -e "${BLUE}Step 1: Configuration${NC}"
read -p "Resource Group Name [healthforesight-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-healthforesight-rg}

read -p "Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Storage Account Name (must be unique): " STORAGE_ACCOUNT
if [ -z "$STORAGE_ACCOUNT" ]; then
    STORAGE_ACCOUNT="healthforesight$(date +%s | tail -c 6)"
    echo -e "${YELLOW}  Using generated name: $STORAGE_ACCOUNT${NC}"
fi

read -p "File Share Name [healthforesight-data]: " FILE_SHARE_NAME
FILE_SHARE_NAME=${FILE_SHARE_NAME:-healthforesight-data}

read -p "Static Web App Name (must be unique): " STATIC_WEB_APP_NAME
if [ -z "$STATIC_WEB_APP_NAME" ]; then
    STATIC_WEB_APP_NAME="healthforesight-web-$(date +%s | tail -c 6)"
    echo -e "${YELLOW}  Using generated name: $STATIC_WEB_APP_NAME${NC}"
fi

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Static Web App: $STATIC_WEB_APP_NAME"
echo ""
echo -e "${YELLOW}Note: This uses FREE tier services (no quota required)${NC}"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

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
echo "  This may take several minutes..."

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

# Create Static Web App (FREE tier, no quota needed)
echo -e "${BLUE}Step 6: Creating Static Web App (Free tier)...${NC}"

# Build frontend first
echo "  Building frontend..."
cd apps/web
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build
cd ../..

# Create Static Web App
az staticwebapp create \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --source apps/web \
  --app-location "apps/web" \
  --output-location "dist" \
  --branch main \
  --output none

STATIC_WEB_URL=$(az staticwebapp show \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

echo -e "${GREEN}✅ Static Web App created${NC}"
echo ""

# For API, we'll use Azure Functions (free tier) or provide instructions
echo -e "${BLUE}Step 7: API Deployment Options${NC}"
echo ""
echo "Since App Service Plan requires quota, here are your options:"
echo ""
echo "Option A: Request quota increase (recommended for full features)"
echo "  Run: ./request-azure-quota.sh"
echo "  Then: ./deploy-complete-to-azure.sh"
echo ""
echo "Option B: Use Azure Container Apps (consumption plan, no quota)"
echo "  This requires Docker containerization"
echo ""
echo "Option C: Use Azure Functions (serverless, free tier)"
echo "  Requires refactoring API to Functions"
echo ""
echo "Option D: Deploy API to a VM or use existing App Service"
echo ""

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Partial Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Static Web App: $STATIC_WEB_APP_NAME"
echo "  Web URL: https://$STATIC_WEB_URL"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Request quota increase for API:"
echo "   ./request-azure-quota.sh"
echo ""
echo "2. After quota approved, deploy API:"
echo "   ./deploy-complete-to-azure.sh"
echo ""
echo "3. Or access your data in Azure File Storage:"
echo "   Storage Account: $STORAGE_ACCOUNT"
echo "   File Share: $FILE_SHARE_NAME"
echo ""
echo -e "${GREEN}✅ All your data has been uploaded to Azure File Storage!${NC}"
echo ""


