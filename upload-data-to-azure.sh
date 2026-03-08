#!/bin/bash
# Upload Data to Azure File Storage Only (No Frontend Build Required)
# Use this while waiting for quota approval

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
echo -e "${BLUE}📦 Upload Data to Azure File Storage${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}This script uploads all your data files to Azure File Storage${NC}"
echo -e "${YELLOW}No quota required - you can do this while waiting for quota approval${NC}"
echo ""

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found${NC}"
    echo "   Run: export PATH=\"/Library/Frameworks/Python.framework/Versions/3.13/bin:\$PATH\""
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

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Upload cancelled."
    exit 0
fi

# Create resource group
echo -e "${BLUE}Step 2: Creating resource group...${NC}"
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo -e "${GREEN}✅ Resource group already exists${NC}"
else
    az group create \
      --name $RESOURCE_GROUP \
      --location $LOCATION \
      --output none
    echo -e "${GREEN}✅ Resource group created${NC}"
fi
echo ""

# Create storage account
echo -e "${BLUE}Step 3: Creating storage account...${NC}"
if az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo -e "${GREEN}✅ Storage account already exists${NC}"
else
    az storage account create \
      --resource-group $RESOURCE_GROUP \
      --name $STORAGE_ACCOUNT \
      --location $LOCATION \
      --sku Standard_LRS \
      --kind StorageV2 \
      --output none
    echo -e "${GREEN}✅ Storage account created${NC}"
fi

STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

# Create file share
echo -e "${BLUE}Step 4: Creating file share...${NC}"
if az storage share show \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE_NAME &>/dev/null; then
    echo -e "${GREEN}✅ File share already exists${NC}"
else
    az storage share create \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --name $FILE_SHARE_NAME \
      --quota 100 \
      --output none
    echo -e "${GREEN}✅ File share created${NC}"
fi
echo ""

# Upload data
echo -e "${BLUE}Step 5: Uploading data files...${NC}"
echo "  This may take several minutes depending on data size..."
echo ""

TOTAL_FILES=0
UPLOADED_FILES=0

# Function to upload directory
upload_directory() {
    local SOURCE_DIR="$1"
    local DEST_PATH="$2"
    local DIR_NAME=$(basename "$SOURCE_DIR")
    
    if [ ! -d "$SOURCE_DIR" ]; then
        echo -e "  ${YELLOW}⚠️  Directory not found: $SOURCE_DIR${NC}"
        return 1
    fi
    
    # Count files
    FILE_COUNT=$(find "$SOURCE_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$FILE_COUNT" -eq 0 ]; then
        echo -e "  ${YELLOW}  No files to upload in $DIR_NAME${NC}"
        return 0
    fi
    
    echo -e "  ${BLUE}Uploading: $DIR_NAME → $DEST_PATH ($FILE_COUNT files)${NC}"
    
    az storage file upload-batch \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --source "$SOURCE_DIR" \
      --destination $FILE_SHARE_NAME \
      --destination-path "$DEST_PATH" \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
        echo -e "  ${YELLOW}  ⚠️  Some files may have failed to upload${NC}"
    }
    
    UPLOADED_FILES=$((UPLOADED_FILES + FILE_COUNT))
    echo -e "  ${GREEN}  ✅ Uploaded $DIR_NAME ($FILE_COUNT files)${NC}"
    return 0
}

# Upload main data directory
if [ -d "apps/api/data" ]; then
    upload_directory "apps/api/data" "data"
    echo ""
fi

# Upload target data model
if [ -d "apps/api/data/target_data_model" ]; then
    upload_directory "apps/api/data/target_data_model" "target_data_model"
    echo ""
fi

# Upload source data
if [ -d "data/source_data" ]; then
    upload_directory "data/source_data" "source_data"
    echo ""
fi

# Upload synthetic data if exists
if [ -d "data/source_data/synthetic" ]; then
    upload_directory "data/source_data/synthetic" "source_data/synthetic"
    echo ""
fi

echo -e "${GREEN}✅ Data upload complete!${NC}"
echo ""

# Verify uploads
echo -e "${BLUE}Step 6: Verifying uploads...${NC}"

# Count files in Azure
REMOTE_COUNT=$(az storage file list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --share-name $FILE_SHARE_NAME \
  --recursive \
  --query "[?type=='File'].name" -o tsv 2>/dev/null | wc -l | tr -d ' ' || echo "0")

echo "  Total files uploaded: $REMOTE_COUNT"
echo ""

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Data Upload Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Upload Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Total Files: $REMOTE_COUNT"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Request App Service Plan quota:"
echo "   - Go to: https://portal.azure.com/#view/Microsoft_Azure_Support/NewSupportRequestV3Blade"
echo "   - Select 'Function or Web App (Windows and Linux)' as quota type"
echo ""
echo "2. After quota approved, deploy API:"
echo "   ./deploy-complete-to-azure.sh"
echo ""
echo "3. View your data in Azure Portal:"
echo "   https://portal.azure.com"
echo "   → Storage accounts → $STORAGE_ACCOUNT → File shares → $FILE_SHARE_NAME"
echo ""
echo -e "${GREEN}✅ All your data is now safely stored in Azure File Storage!${NC}"
echo ""


