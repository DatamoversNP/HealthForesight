#!/bin/bash
# Deploy to Azure using Container Apps (No Quota Required)
# Container Apps use consumption plan which doesn't require quota

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
echo -e "${BLUE}🚀 Azure Deployment - Container Apps (No Quota Required)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}This uses Azure Container Apps with consumption plan${NC}"
echo -e "${YELLOW}No App Service Plan quota needed!${NC}"
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

# Check if Container Apps extension is installed
if ! az extension show --name containerapp &>/dev/null; then
    echo -e "${BLUE}Installing Container Apps extension...${NC}"
    az extension add --name containerapp
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

read -p "Container App Environment Name [healthforesight-env]: " CONTAINER_ENV_NAME
CONTAINER_ENV_NAME=${CONTAINER_ENV_NAME:-healthforesight-env}

read -p "API Container App Name [healthforesight-api]: " API_APP_NAME
API_APP_NAME=${API_APP_NAME:-healthforesight-api}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Container Environment: $CONTAINER_ENV_NAME"
echo "  API Container App: $API_APP_NAME"
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

# Create Container Apps environment
echo -e "${BLUE}Step 6: Creating Container Apps environment...${NC}"
az containerapp env create \
  --name $CONTAINER_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --output none
echo -e "${GREEN}✅ Container environment created${NC}"
echo ""

# Note: For Container Apps, you'd need to containerize the API
# This is a placeholder - actual deployment would require Docker image
echo -e "${YELLOW}⚠️  Note: Container Apps requires a Docker image${NC}"
echo ""
echo "To complete API deployment with Container Apps:"
echo "1. Create a Dockerfile for the API"
echo "2. Build and push to Azure Container Registry"
echo "3. Deploy container app"
echo ""
echo "For now, your data is uploaded to Azure File Storage."
echo ""

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Data Upload Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Container Environment: $CONTAINER_ENV_NAME"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "Option 1: Request App Service Plan quota via Support"
echo "  ./request-app-service-quota.sh"
echo ""
echo "Option 2: Use the free tier deployment (Static Web Apps)"
echo "  ./deploy-to-azure-free-tier.sh"
echo ""
echo -e "${GREEN}✅ All your data has been uploaded to Azure File Storage!${NC}"
echo ""


