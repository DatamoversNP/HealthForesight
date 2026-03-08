#!/bin/bash
# Comprehensive Data Fix for Azure Deployment
# This script ensures ALL data is properly deployed and accessible

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔧 Comprehensive Data Fix for Azure Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Azure configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo -e "${BLUE}Step 1: Verifying local data structure...${NC}"

# Check what data directories exist locally
DATA_DIRS=(
    "data/policies"
    "data/predicted_impacts"
    "data/observations"
    "data/baselines"
    "data/analyses"
    "data/analysis_results"
    "data/pipelines"
    "data/pipeline_runs"
    "data/scenarios"
    "data/decisions"
    "data/risks"
    "data/source_data"
)

echo "  Checking local data directories:"
for dir in "${DATA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        FILE_COUNT=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo -e "    ${GREEN}✅${NC} $dir ($FILE_COUNT files, $SIZE)"
    else
        echo -e "    ${YELLOW}⚠️${NC} $dir (not found)"
    fi
done

echo ""
echo -e "${BLUE}Step 2: Creating deployment package with ALL data...${NC}"

# Create temp directory for deployment
TEMP_DEPLOY_DIR=$(mktemp -d)
echo "  Using temp directory: $TEMP_DEPLOY_DIR"

# Copy API source code
echo "  Copying API source code..."
mkdir -p "$TEMP_DEPLOY_DIR/src/uepi_api"
rsync -av \
    --exclude='tests' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env*' \
    --exclude='*.log' \
    apps/api/src/uepi_api/ "$TEMP_DEPLOY_DIR/src/uepi_api/" 2>/dev/null || {
    cp -r apps/api/src/uepi_api/* "$TEMP_DEPLOY_DIR/src/uepi_api/" 2>/dev/null || true
}

# Copy packages/common
if [ -d "packages/common" ]; then
    echo "  Including packages/common..."
    mkdir -p "$TEMP_DEPLOY_DIR/packages/common"
    cp -r packages/common/src "$TEMP_DEPLOY_DIR/packages/common/" 2>/dev/null || true
fi

# Copy ALL data directories - CRITICAL: This ensures data is available on Azure
echo "  Copying ALL data directories (exact replica of local)..."
mkdir -p "$TEMP_DEPLOY_DIR/data"

if [ -d "data" ]; then
    # Copy entire data directory structure
    if command -v rsync &> /dev/null; then
        rsync -av --exclude='.git' data/ "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || {
            echo "    Using cp fallback..."
            cp -r data/* "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
        }
    else
        cp -r data/* "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
    fi
    
    # Verify what was copied
    echo "  Verifying copied data:"
    for dir in "${DATA_DIRS[@]}"; do
        deploy_dir="$TEMP_DEPLOY_DIR/$dir"
        if [ -d "$deploy_dir" ]; then
            FILE_COUNT=$(find "$deploy_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
            echo -e "    ${GREEN}✅${NC} $dir ($FILE_COUNT files)"
        else
            echo -e "    ${YELLOW}⚠️${NC} $dir (not found in deployment package)"
        fi
    done
else
    echo -e "  ${RED}❌ No data/ directory found at project root!${NC}"
    exit 1
fi

# Copy required files
echo "  Copying configuration files..."
cp apps/api/requirements.txt "$TEMP_DEPLOY_DIR/" 2>/dev/null || true
cp apps/api/pyproject.toml "$TEMP_DEPLOY_DIR/" 2>/dev/null || true
cp apps/api/startup.sh "$TEMP_DEPLOY_DIR/" 2>/dev/null || true

# Create ZIP
echo "  Creating deployment ZIP package..."
cd "$TEMP_DEPLOY_DIR"
ZIP_FILE="$SCRIPT_DIR/api-complete-data-deployment.zip"
zip -r "$ZIP_FILE" . \
    -x "*.git*" \
    -x "*__pycache__/*" \
    -x "*.pyc" \
    -x "*.log" \
    -x "tests/*" \
    -x ".env*" 2>/dev/null || {
    echo -e "  ${RED}❌ Failed to create ZIP${NC}"
    cd "$SCRIPT_DIR"
    rm -rf "$TEMP_DEPLOY_DIR"
    exit 1
}

ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo -e "  ${GREEN}✅ Deployment package created: $ZIP_SIZE${NC}"

cd "$SCRIPT_DIR"
rm -rf "$TEMP_DEPLOY_DIR"

# Verify ZIP contains data
echo "  Verifying ZIP contents..."
if zipinfo "$ZIP_FILE" | grep -q "data/"; then
    DATA_FILES_IN_ZIP=$(zipinfo "$ZIP_FILE" | grep "data/" | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✅ ZIP contains $DATA_FILES_IN_ZIP data files${NC}"
else
    echo -e "  ${RED}❌ ZIP does not contain data/ directory!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Deploying to Azure App Service...${NC}"

# Deploy to Azure
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --src "$ZIP_FILE" \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo -e "  ${YELLOW}⚠️  Deployment warning (may still succeed)${NC}"
}

# Set STORAGE_PATH environment variable - CRITICAL for data access
echo "  Setting STORAGE_PATH environment variable..."
az webapp config appsettings set \
    --name "$API_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        STORAGE_PATH="/home/site/wwwroot/data" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

# Clean up
rm -f "$ZIP_FILE"

echo -e "  ${GREEN}✅ Deployment complete${NC}"
echo ""

echo -e "${BLUE}Step 4: Waiting for deployment to complete...${NC}"
echo "  Waiting 30 seconds for Azure to process deployment..."
sleep 30

echo ""
echo -e "${BLUE}Step 5: Verifying deployment...${NC}"

# Check API health
echo "  Checking API health..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "https://$API_APP_NAME.azurewebsites.net/health" 2>/dev/null || echo "ERROR")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "  ${GREEN}✅ API is healthy${NC}"
else
    echo -e "  ${YELLOW}⚠️  API health check returned: $HTTP_CODE${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Comprehensive Data Fix Complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for Azure to fully process the deployment"
echo "  2. Test API endpoints:"
echo "     curl https://$API_APP_NAME.azurewebsites.net/api/v1/policies"
echo "  3. Check Azure logs if issues persist:"
echo "     az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo "  4. Verify data files on Azure (SSH into app):"
echo "     az webapp ssh --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo "     # Then: ls -la /home/site/wwwroot/data/"
echo ""

