#!/bin/bash
# Migrate local file-based data to Azure File Storage

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-healthforesightstg9016}"
FILE_SHARE_NAME="${FILE_SHARE_NAME:-healthforesight-data}"
LOCAL_DATA_DIR="${LOCAL_DATA_DIR:-apps/api/data}"

echo "========================================="
echo "📦 Migrating Local Data to Azure File Storage"
echo "========================================="
echo ""
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "File Share: $FILE_SHARE_NAME"
echo "Local Data Directory: $LOCAL_DATA_DIR"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Check if local data directory exists
if [ ! -d "$LOCAL_DATA_DIR" ]; then
    echo "❌ Local data directory not found: $LOCAL_DATA_DIR"
    exit 1
fi

# Get storage account key
echo "Getting storage account key..."
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT_NAME \
    --query "[0].value" \
    --output tsv 2>/dev/null)

if [ -z "$STORAGE_KEY" ]; then
    echo "❌ Failed to get storage account key"
    exit 1
fi

echo "✅ Storage account key retrieved"
echo ""

# Check if file share exists, create if not
echo "Checking if file share exists..."
if ! az storage share exists \
    --account-name $STORAGE_ACCOUNT_NAME \
    --account-key "$STORAGE_KEY" \
    --name $FILE_SHARE_NAME \
    --query "exists" \
    --output tsv 2>/dev/null | grep -q "true"; then
    echo "Creating file share: $FILE_SHARE_NAME"
    az storage share create \
        --account-name $STORAGE_ACCOUNT_NAME \
        --account-key "$STORAGE_KEY" \
        --name $FILE_SHARE_NAME \
        --quota 100 \
        --output none
    echo "✅ File share created"
else
    echo "✅ File share already exists"
fi
echo ""

# Run migration
echo "Starting data migration..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3."
    exit 1
fi

# Check if azure-storage-file-share is installed
if ! python3 -c "import azure.storage.fileshare" 2>/dev/null; then
    echo "Installing azure-storage-file-share..."
    pip3 install azure-storage-file-share --quiet
fi

# Run migration script (use the Python file in the same directory)
MIGRATE_SCRIPT="$SCRIPT_DIR/migrate-data-to-azure.py"
python3 "$MIGRATE_SCRIPT" \
    "$STORAGE_ACCOUNT_NAME" \
    "$STORAGE_KEY" \
    "$FILE_SHARE_NAME" \
    "$PROJECT_ROOT/$LOCAL_DATA_DIR"

echo ""
echo "✅ Data migration completed!"
echo ""
echo "Next steps:"
echo "1. Verify the API is configured to use Azure File Storage:"
echo "   - USE_AZURE_FILE_STORAGE=true"
echo "   - AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME"
echo "   - AZURE_STORAGE_ACCOUNT_KEY=<set in Azure App Service>"
echo "   - AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE_NAME"
echo ""
echo "2. Restart the API app service to load the migrated data"
echo ""

