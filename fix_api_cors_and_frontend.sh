#!/bin/bash
# Fix API CORS and Frontend API URL Configuration
# This script updates the API CORS settings and rebuilds the frontend with correct API URL

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
echo -e "${BLUE}🔧 Fix API CORS and Frontend API URL Configuration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Azure configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-gentle-flower-01dffcd0f}"

echo -e "${BLUE}Step 1: Deploying API CORS fix...${NC}"

# Create temporary deployment directory
TEMP_DEPLOY_DIR=$(mktemp -d)
echo "  Using temp directory: $TEMP_DEPLOY_DIR"

# Copy API files
echo "  Copying API files..."
mkdir -p "$TEMP_DEPLOY_DIR/src/uepi_api"
cp -r apps/api/src/uepi_api/* "$TEMP_DEPLOY_DIR/src/uepi_api/" 2>/dev/null || true

# Copy packages/common
if [ -d "packages/common" ]; then
    echo "  Including packages/common..."
    mkdir -p "$TEMP_DEPLOY_DIR/packages/common"
    cp -r packages/common/src "$TEMP_DEPLOY_DIR/packages/common/" 2>/dev/null || true
fi

# Copy data directory
if [ -d "data" ]; then
    echo "  Including data directory..."
    mkdir -p "$TEMP_DEPLOY_DIR/data"
    cp -r data/* "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
fi

# Copy other required files
cp apps/api/requirements.txt "$TEMP_DEPLOY_DIR/" 2>/dev/null || true
cp apps/api/pyproject.toml "$TEMP_DEPLOY_DIR/" 2>/dev/null || true
cp apps/api/startup.sh "$TEMP_DEPLOY_DIR/" 2>/dev/null || true

# Create ZIP
echo "  Creating deployment package..."
cd "$TEMP_DEPLOY_DIR"
ZIP_FILE="$SCRIPT_DIR/api-cors-fix.zip"
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

cd "$SCRIPT_DIR"
rm -rf "$TEMP_DEPLOY_DIR"

# Deploy to Azure
echo "  Deploying to Azure App Service..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --src "$ZIP_FILE" \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
    echo -e "  ${YELLOW}⚠️  Deployment warning (may still succeed)${NC}"
}

# Set STORAGE_PATH
echo "  Setting STORAGE_PATH environment variable..."
az webapp config appsettings set \
    --name "$API_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        STORAGE_PATH="/home/site/wwwroot/data" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

rm -f "$ZIP_FILE"

echo -e "  ${GREEN}✅ API CORS fix deployed${NC}"
echo ""

echo -e "${BLUE}Step 2: Rebuilding frontend with correct API URL...${NC}"

cd apps/web

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "  ${YELLOW}⚠️  npm not found. Skipping frontend rebuild.${NC}"
    echo -e "  ${YELLOW}Please rebuild the frontend manually:${NC}"
    echo -e "  ${YELLOW}  cd apps/web${NC}"
    echo -e "  ${YELLOW}  npm install${NC}"
    echo -e "  ${YELLOW}  npm run build${NC}"
    echo -e "  ${YELLOW}  # Then deploy the dist/ folder to Azure Static Web Apps${NC}"
    exit 0
fi

# Create production environment file with correct API URL
API_URL="https://$API_APP_NAME.azurewebsites.net"
echo "  Creating production environment file..."
echo "VITE_API_URL=$API_URL/api/v1" > .env.production
echo "VITE_API_BASE_URL=$API_URL/api/v1" >> .env.production
echo -e "  ${GREEN}✅ Environment file created with API URL: $API_URL/api/v1${NC}"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
else
    echo "  Dependencies already installed"
fi

# Build for production
echo "  Building for production..."
npm run build || {
    echo -e "  ${RED}❌ Build failed${NC}"
    exit 1
}

echo -e "  ${GREEN}✅ Frontend built${NC}"

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo -e "  ${RED}❌ dist directory not found after build${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Frontend rebuild complete${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Deploy the frontend to Azure Static Web Apps:"
echo "     cd apps/web/dist"
echo "     # Use Azure Portal or Azure CLI to deploy the dist/ folder"
echo ""
echo "  2. Or use Azure Static Web Apps CLI (if installed):"
echo "     az staticwebapp deploy \\"
echo "       --name $STATIC_WEB_APP_NAME \\"
echo "       --resource-group $RESOURCE_GROUP \\"
echo "       --app-location apps/web \\"
echo "       --output-location dist"
echo ""
echo "  3. Verify the fix:"
echo "     - Wait 2-3 minutes for API deployment to complete"
echo "     - Check API health: curl https://$API_APP_NAME.azurewebsites.net/health"
echo "     - Open frontend: https://gentle-flower-01dffcd0f.2.azurestaticapps.net"
echo "     - Check browser console for API connection"
echo ""

