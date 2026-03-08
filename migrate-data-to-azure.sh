#!/bin/bash
# Automated Data Migration Script for Azure File Storage
# Migrates all data from local file system to Azure File Storage

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
echo -e "${BLUE}📦 Azure File Storage - Data Migration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login...${NC}"
    az login
fi

echo -e "${YELLOW}Step 1: Configuration${NC}"
read -p "Resource Group Name [healthforesight-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-healthforesight-rg}

read -p "Storage Account Name: " STORAGE_ACCOUNT
if [ -z "$STORAGE_ACCOUNT" ]; then
    echo -e "${RED}❌ Storage account name is required${NC}"
    exit 1
fi

read -p "File Share Name [healthforesight-data]: " FILE_SHARE_NAME
FILE_SHARE_NAME=${FILE_SHARE_NAME:-healthforesight-data}

read -p "Local Data Directory [apps/api/data]: " LOCAL_DATA_DIR
LOCAL_DATA_DIR=${LOCAL_DATA_DIR:-apps/api/data}

read -p "Local Target Data Model Directory [apps/api/target_data_model]: " LOCAL_TARGET_DIR
LOCAL_TARGET_DIR=${LOCAL_TARGET_DIR:-apps/api/target_data_model}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Local Data Directory: $LOCAL_DATA_DIR"
echo "  Local Target Data Model Directory: $LOCAL_TARGET_DIR"
echo ""

read -p "Continue with migration? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Migration cancelled."
    exit 0
fi

echo ""

# Get storage key
echo -e "${BLUE}Step 2: Getting storage account key...${NC}"
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

if [ -z "$STORAGE_KEY" ]; then
    echo -e "${RED}❌ Failed to get storage account key${NC}"
    exit 1
fi

echo -e "  ${GREEN}✅ Storage key obtained${NC}"
echo ""

# Verify file share exists
echo -e "${BLUE}Step 3: Verifying file share...${NC}"
if ! az storage share exists \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name $FILE_SHARE_NAME \
  --query exists -o tsv | grep -q "true"; then
    echo "  Creating file share..."
    az storage share create \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --name $FILE_SHARE_NAME \
      --output none
    echo -e "  ${GREEN}✅ File share created${NC}"
else
    echo -e "  ${GREEN}✅ File share exists${NC}"
fi
echo ""

# Function to upload directory recursively
upload_directory() {
    local SOURCE_DIR="$1"
    local DEST_PATH="$2"
    local DIR_NAME=$(basename "$SOURCE_DIR")
    
    if [ ! -d "$SOURCE_DIR" ]; then
        echo -e "  ${YELLOW}⚠️  Directory not found: $SOURCE_DIR${NC}"
        return 1
    fi
    
    echo -e "${BLUE}  Uploading: $DIR_NAME → $DEST_PATH${NC}"
    
    # Count files
    FILE_COUNT=$(find "$SOURCE_DIR" -type f | wc -l | tr -d ' ')
    if [ "$FILE_COUNT" -eq 0 ]; then
        echo -e "  ${YELLOW}  No files to upload in $DIR_NAME${NC}"
        return 0
    fi
    
    echo "  Found $FILE_COUNT files"
    
    # Upload using Azure CLI
    az storage file upload-batch \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --source "$SOURCE_DIR" \
      --destination "$FILE_SHARE_NAME" \
      --destination-path "$DEST_PATH" \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
        echo -e "  ${YELLOW}  ⚠️  Some files may have failed to upload${NC}"
    }
    
    echo -e "  ${GREEN}  ✅ Uploaded $DIR_NAME${NC}"
    return 0
}

# Function to upload single directory structure
upload_single_dir() {
    local SOURCE_DIR="$1"
    local DEST_PATH="$2"
    
    echo -e "${BLUE}  Uploading directory structure: $SOURCE_DIR → $DEST_PATH${NC}"
    
    # Upload each subdirectory individually to maintain structure
    if [ -d "$SOURCE_DIR" ]; then
        for SUBDIR in "$SOURCE_DIR"/*; do
            if [ -d "$SUBDIR" ]; then
                SUBDIR_NAME=$(basename "$SUBDIR")
                upload_directory "$SUBDIR" "$DEST_PATH/$SUBDIR_NAME"
            elif [ -f "$SUBDIR" ]; then
                # Upload single file
                FILE_NAME=$(basename "$SUBDIR")
                az storage file upload \
                  --account-name $STORAGE_ACCOUNT \
                  --account-key $STORAGE_KEY \
                  --share-name $FILE_SHARE_NAME \
                  --source "$SUBDIR" \
                  --path "$DEST_PATH/$FILE_NAME" \
                  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
            fi
        done
    fi
}

# Migrate data directory
echo -e "${BLUE}Step 4: Migrating data directory...${NC}"
if [ -d "$LOCAL_DATA_DIR" ]; then
    # Upload main data directory structure
    upload_directory "$LOCAL_DATA_DIR" "data"
    
    # Upload specific subdirectories to ensure structure
    echo ""
    echo -e "${BLUE}  Uploading data subdirectories:${NC}"
    
    DATA_SUBDIRS=(
        "baselines"
        "observations"
        "policies"
        "analyses"
        "analysis_result_indices"
        "learning"
        "scorecards"
        "ingestions"
        "pipeline_runs"
        "pipelines"
        "curated"
        "users"
        "tenants"
        "scenario_accuracy"
        "exports"
    )
    
    for SUBDIR in "${DATA_SUBDIRS[@]}"; do
        if [ -d "$LOCAL_DATA_DIR/$SUBDIR" ]; then
            upload_directory "$LOCAL_DATA_DIR/$SUBDIR" "data/$SUBDIR"
        fi
    done
    
    echo -e "  ${GREEN}✅ Data directory migration complete${NC}"
else
    echo -e "  ${YELLOW}⚠️  Data directory not found: $LOCAL_DATA_DIR${NC}"
fi
echo ""

# Migrate target data model directory
echo -e "${BLUE}Step 5: Migrating target data model directory...${NC}"
if [ -d "$LOCAL_TARGET_DIR" ]; then
    upload_directory "$LOCAL_TARGET_DIR" "target_data_model"
    echo -e "  ${GREEN}✅ Target data model migration complete${NC}"
else
    echo -e "  ${YELLOW}⚠️  Target data model directory not found: $LOCAL_TARGET_DIR${NC}"
fi
echo ""

# Verify uploads
echo -e "${BLUE}Step 6: Verifying uploads...${NC}"

verify_upload() {
    local REMOTE_PATH="$1"
    local LOCAL_PATH="$2"
    
    if [ ! -d "$LOCAL_PATH" ]; then
        return 0  # Skip if local doesn't exist
    fi
    
    # Count local files
    LOCAL_COUNT=$(find "$LOCAL_PATH" -type f | wc -l | tr -d ' ')
    
    # List remote files
    REMOTE_COUNT=$(az storage file list \
      --account-name $STORAGE_ACCOUNT \
      --account-key $STORAGE_KEY \
      --share-name $FILE_SHARE_NAME \
      --path "$REMOTE_PATH" \
      --recursive \
      --query "[?type=='File'].name" -o tsv 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    
    if [ "$LOCAL_COUNT" -eq 0 ]; then
        return 0  # Skip empty directories
    fi
    
    echo "  $REMOTE_PATH: Local=$LOCAL_COUNT files, Remote=$REMOTE_COUNT files"
    
    if [ "$LOCAL_COUNT" -eq "$REMOTE_COUNT" ]; then
        echo -e "    ${GREEN}✅ Verified (all files uploaded)${NC}"
        return 0
    else
        echo -e "    ${YELLOW}⚠️  Mismatch (may need re-upload)${NC}"
        return 1
    fi
}

# Verify data directory
if [ -d "$LOCAL_DATA_DIR" ]; then
    verify_upload "data" "$LOCAL_DATA_DIR"
    
    # Verify key subdirectories
    verify_upload "data/baselines" "$LOCAL_DATA_DIR/baselines"
    verify_upload "data/observations" "$LOCAL_DATA_DIR/observations"
    verify_upload "data/policies" "$LOCAL_DATA_DIR/policies"
    verify_upload "data/analyses" "$LOCAL_DATA_DIR/analyses"
fi

# Verify target data model
if [ -d "$LOCAL_TARGET_DIR" ]; then
    verify_upload "target_data_model" "$LOCAL_TARGET_DIR"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Data Migration Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Migration Summary:${NC}"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $FILE_SHARE_NAME"
echo "  Data Location: data/"
echo "  Target Data Models: target_data_model/"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Verify data in Azure Portal:"
echo "   https://portal.azure.com"
echo "   → Storage accounts → $STORAGE_ACCOUNT → File shares → $FILE_SHARE_NAME"
echo ""
echo "2. Update app configuration:"
echo "   Make sure USE_AZURE_FILE_STORAGE=true is set in app settings"
echo ""
echo "3. Test your application:"
echo "   The app should now read data from Azure File Storage"
echo ""
echo "4. List uploaded files:"
echo "   az storage file list \\"
echo "     --account-name $STORAGE_ACCOUNT \\"
echo "     --account-key <key> \\"
echo "     --share-name $FILE_SHARE_NAME \\"
echo "     --path data \\"
echo "     --recursive \\"
echo "     --output table"
echo ""
echo -e "${GREEN}✅ All data has been migrated to Azure File Storage!${NC}"
echo ""
