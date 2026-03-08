#!/bin/bash
# Deploy the critical metadata fix to Azure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Deploying Critical Metadata Fix to Azure"
echo "============================================"
echo ""

# Step 1: Verify fix is in place
echo "Step 1: Verifying code fix..."
if grep -q "Always use metadata value - individual files are source of truth" apps/api/src/uepi_api/storage_policies.py; then
    echo "✅ Fix verified in storage_policies.py"
else
    echo "❌ Fix NOT found! Aborting."
    exit 1
fi

# Step 2: Create deployment package
echo ""
echo "Step 2: Creating deployment package..."
TEMP_DEPLOY_DIR=$(mktemp -d)
echo "   Using temp dir: $TEMP_DEPLOY_DIR"

# Copy API files
echo "   Copying API files..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    apps/api/ "$TEMP_DEPLOY_DIR/" \
    --exclude='apps/api/data/target_data_model' \
    --exclude='apps/api/data/cost_tracking' \
    2>/dev/null || true

# Copy packages/common
if [ -d "packages/common" ]; then
    echo "   Copying packages/common..."
    rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
        packages/common/ "$TEMP_DEPLOY_DIR/packages/common/" 2>/dev/null || true
fi

# Copy ALL data files (including policy_*.json with metadata)
echo "   Copying data files..."
mkdir -p "$TEMP_DEPLOY_DIR/data"
rsync -av --exclude='.git' data/ "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true

# Verify policy files are included
POLICY_COUNT=$(find "$TEMP_DEPLOY_DIR/data" -name "policy_*.json" | wc -l | tr -d ' ')
echo "   Found $POLICY_COUNT policy files in deployment package"

if [ "$POLICY_COUNT" -eq "0" ]; then
    echo "   ⚠️  WARNING: No policy files found! Checking source..."
    SOURCE_COUNT=$(find data -name "policy_*.json" | wc -l | tr -d ' ')
    echo "   Source has $SOURCE_COUNT policy files"
    if [ "$SOURCE_COUNT" -gt "0" ]; then
        echo "   Copying policy files explicitly..."
        cp data/policy_*.json "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
        POLICY_COUNT=$(find "$TEMP_DEPLOY_DIR/data" -name "policy_*.json" | wc -l | tr -d ' ')
        echo "   Now have $POLICY_COUNT policy files"
    fi
fi

# Verify one policy file has metadata
if [ "$POLICY_COUNT" -gt "0" ]; then
    SAMPLE_POLICY=$(find "$TEMP_DEPLOY_DIR/data" -name "policy_*.json" | head -1)
    if python3 -c "import json; d=json.load(open('$SAMPLE_POLICY')); print('Assumptions:', len(d.get('metadata', {}).get('assumptions', [])))" 2>/dev/null; then
        echo "   ✅ Sample policy has metadata"
    else
        echo "   ⚠️  WARNING: Sample policy may not have metadata"
    fi
fi

# Create ZIP
ZIP_FILE="api-deployment-metadata-fix.zip"
echo ""
echo "Step 3: Creating ZIP file..."
cd "$TEMP_DEPLOY_DIR"
zip -r "$SCRIPT_DIR/$ZIP_FILE" . -q
cd "$SCRIPT_DIR"
echo "   ✅ Created $ZIP_FILE ($(du -h $ZIP_FILE | cut -f1))"

# Step 4: Deploy to Azure
echo ""
echo "Step 4: Deploying to Azure..."
RESOURCE_GROUP="healthforesight-rg"
APP_NAME="healthforesight-api-9016"

if ! az account show &>/dev/null; then
    echo "   ⚠️  Not logged in to Azure. Please login first:"
    echo "      az login"
    exit 1
fi

echo "   Deploying ZIP to $APP_NAME..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --src "$ZIP_FILE" \
    --timeout 600

echo ""
echo "Step 5: Setting STORAGE_PATH environment variable..."
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --settings STORAGE_PATH="/home/site/wwwroot/data" \
    --output none

echo ""
echo "Step 6: Restarting app..."
az webapp restart \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --output none

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Waiting 30 seconds for app to start..."
sleep 30

echo ""
echo "Step 7: Verifying deployment..."
HEALTH_URL="https://healthforesight-api-9016.azurewebsites.net/health"
if curl -s "$HEALTH_URL" | grep -q "healthy"; then
    echo "   ✅ API is healthy"
else
    echo "   ⚠️  API health check failed - check logs"
fi

echo ""
echo "============================================"
echo "Deployment Summary:"
echo "  - Fixed metadata copying in storage_policies.py"
echo "  - Deployed $POLICY_COUNT policy files"
echo "  - Set STORAGE_PATH=/home/site/wwwroot/data"
echo "  - Restarted app"
echo ""
echo "Test with: ./test_metadata_after_deployment.sh"
echo ""

# Cleanup
rm -rf "$TEMP_DEPLOY_DIR"
echo "Cleaned up temp directory"

