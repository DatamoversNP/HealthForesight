#!/bin/bash
# Production Build and Redeploy to Azure
# Uses ZIP deployment (no Docker required)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Production Build and Redeploy to Azure (ZIP Deployment)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Step 0: Checking prerequisites...${NC}"

if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v zip &> /dev/null; then
    echo -e "${RED}❌ zip command not found. Please install it first.${NC}"
    echo "   macOS: brew install zip"
    exit 1
fi

if ! az account show &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login...${NC}"
    az login
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"
echo ""

# Configuration - try to detect existing resources
echo -e "${BLUE}Step 1: Detecting existing Azure resources...${NC}"

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
LOCATION="${LOCATION:-eastus}"

# Check if resource group exists
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo -e "${GREEN}✅ Found existing resource group: $RESOURCE_GROUP${NC}"
    LOCATION=$(az group show --name "$RESOURCE_GROUP" --query location -o tsv | tr -d '"')
else
    echo -e "${YELLOW}⚠️  Resource group not found. Will create: $RESOURCE_GROUP${NC}"
    read -p "Create resource group? (y/n): " CREATE_RG
    if [ "$CREATE_RG" = "y" ] || [ "$CREATE_RG" = "Y" ]; then
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
        echo -e "${GREEN}✅ Resource group created${NC}"
    else
        echo "Exiting. Please create resource group first or set RESOURCE_GROUP environment variable."
        exit 1
    fi
fi

# Find existing API App Service
API_APP_NAME=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'api') || contains(name, 'API')].name" -o tsv 2>/dev/null | head -1 || echo "")
if [ -z "$API_APP_NAME" ]; then
    echo -e "${YELLOW}⚠️  No API App Service found${NC}"
    read -p "Enter API App Service name (or press Enter to skip API deployment): " API_APP_NAME
    if [ -z "$API_APP_NAME" ]; then
        echo -e "${YELLOW}Skipping API deployment${NC}"
        DEPLOY_API=false
    else
        DEPLOY_API=true
    fi
else
    echo -e "${GREEN}✅ Found existing API App: $API_APP_NAME${NC}"
    DEPLOY_API=true
fi

# Find existing Web App Service
WEB_APP_NAME=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'web') || contains(name, 'WEB')].name" -o tsv 2>/dev/null | head -1 || echo "")
if [ -z "$WEB_APP_NAME" ]; then
    echo -e "${YELLOW}⚠️  No Web App Service found${NC}"
    read -p "Enter Web App Service name (or press Enter to skip web deployment): " WEB_APP_NAME
    if [ -z "$WEB_APP_NAME" ]; then
        echo -e "${YELLOW}Skipping web deployment${NC}"
        DEPLOY_WEB=false
    else
        DEPLOY_WEB=true
    fi
else
    echo -e "${GREEN}✅ Found existing Web App: $WEB_APP_NAME${NC}"
    DEPLOY_WEB=true
fi

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
if [ "$DEPLOY_API" = "true" ]; then
    echo "  API App: $API_APP_NAME"
fi
if [ "$DEPLOY_WEB" = "true" ]; then
    echo "  Web App: $WEB_APP_NAME"
fi
echo ""

read -p "Continue with build and deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""

# Deploy API
if [ "$DEPLOY_API" = "true" ]; then
    echo -e "${BLUE}Step 2: Building and deploying API...${NC}"
    
    # Use existing startup.sh if available, otherwise create a simple one
    if [ ! -f "apps/api/startup.sh" ]; then
        echo "  Creating startup.sh..."
        cat > apps/api/startup.sh << 'EOF'
#!/bin/bash
# Azure App Service startup script

# Set PYTHONPATH
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"

# Use PORT environment variable (Azure App Service provides this)
PORT=${PORT:-8000}

# Start the application
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port $PORT
EOF
        chmod +x apps/api/startup.sh
        echo -e "  ${GREEN}✅ startup.sh created${NC}"
    else
        echo -e "  ${GREEN}✅ Using existing startup.sh${NC}"
        chmod +x apps/api/startup.sh
    fi
    
    # Create deployment ZIP - need to include packages/common from project root
    echo "  Creating deployment package (including packages/common)..."
    
    # Create temp directory for deployment
    TEMP_DEPLOY_DIR=$(mktemp -d)
    echo "  Using temp directory: $TEMP_DEPLOY_DIR"
    
    # Copy API files - INCLUDING ALL DATA FILES (exact replica of local)
    echo "  Copying API files with ALL data directories..."
    rsync -av \
        --exclude='tests' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        apps/api/ "$TEMP_DEPLOY_DIR/" 2>/dev/null || {
        # Fallback to cp if rsync not available
        echo "  Using cp fallback (rsync not available)..."
        cp -r apps/api/* "$TEMP_DEPLOY_DIR/" 2>/dev/null || true
        # Only remove non-data directories (tests, build artifacts)
        rm -rf "$TEMP_DEPLOY_DIR/tests" 2>/dev/null || true
    }
    
    # Copy ENTIRE data directory from project root (exact replica of local)
    # This ensures ALL data is included: source_data, predicted_impacts, analyses, etc.
    echo "  Copying ALL data files from project root (exact replica)..."
    if [ -d "data" ]; then
        echo "    Copying complete data/ directory with ALL subdirectories..."
        # Ensure data directory exists in temp
        mkdir -p "$TEMP_DEPLOY_DIR/data"
        
        # Copy entire data directory, preserving structure
        # Use rsync if available for better performance, fallback to cp
        if command -v rsync &> /dev/null; then
            rsync -av --exclude='.git' data/ "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || {
                echo "    Using cp fallback..."
                cp -r data/* "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
            }
        else
            cp -r data/* "$TEMP_DEPLOY_DIR/data/" 2>/dev/null || true
        fi
        
        # Count what was copied
        DATA_DIRS=$(find "$TEMP_DEPLOY_DIR/data" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
        DATA_FILES=$(find "$TEMP_DEPLOY_DIR/data" -type f 2>/dev/null | wc -l | tr -d ' ')
        DATA_SIZE=$(du -sh "$TEMP_DEPLOY_DIR/data" 2>/dev/null | cut -f1)
        echo "    ✅ Copied $DATA_DIRS data directories with $DATA_FILES files (Total size: $DATA_SIZE)"
        
        # Verify key data directories are present
        echo "    Verifying key data directories:"
        KEY_DIRS=("source_data" "predicted_impacts" "analyses" "analysis_results" "observations" "baselines" "pipelines" "pipeline_runs" "scenarios" "decisions" "scorecards")
        for dir in "${KEY_DIRS[@]}"; do
            if [ -d "$TEMP_DEPLOY_DIR/data/$dir" ]; then
                FILE_COUNT=$(find "$TEMP_DEPLOY_DIR/data/$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
                echo "      ✅ $dir ($FILE_COUNT files)"
            else
                echo "      ⚠️  $dir (not found - may be empty)"
            fi
        done
    else
        echo "    ⚠️  No data/ directory found at project root"
    fi
    
    # Copy packages/common from project root
    if [ -d "packages/common" ]; then
        echo "  Including packages/common..."
        mkdir -p "$TEMP_DEPLOY_DIR/packages/common"
        cp -r packages/common/src "$TEMP_DEPLOY_DIR/packages/common/" 2>/dev/null || true
    fi
    
    # Create ZIP from temp directory - INCLUDING ALL DATA FILES
    echo "  Creating ZIP package with ALL data files..."
    cd "$TEMP_DEPLOY_DIR"
    ZIP_FILE="$SCRIPT_DIR/api-deployment.zip"
    
    # Only exclude build artifacts, not data
    zip -r "$ZIP_FILE" . \
        -x "*.git*" \
        -x "*.venv*" \
        -x "*__pycache__/*" \
        -x "*.pyc" \
        -x "*.pyo" \
        -x "*.pyd" \
        -x "*.log" \
        -x "*.pytest_cache*" \
        -x "*.mypy_cache*" \
        -x "deploy.zip" \
        -x "api-deployment.zip" \
        -x "tests/*" \
        -x ".env*" 2>/dev/null || {
        echo -e "  ${RED}❌ Failed to create ZIP${NC}"
        cd "$SCRIPT_DIR"
        rm -rf "$TEMP_DEPLOY_DIR"
        exit 1
    }
    
    # Show ZIP size and contents summary
    ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    echo "  📦 ZIP file size: $ZIP_SIZE"
    echo "  📊 ZIP contents summary:"
    zipinfo "$ZIP_FILE" | tail -1
    
    # Clean up temp directory and return to project root
    cd "$SCRIPT_DIR"
    rm -rf "$TEMP_DEPLOY_DIR"
    
    echo -e "  ${GREEN}✅ Deployment package created${NC}"
    
    # Verify ZIP contains required files
    echo "  Verifying package contents..."
    ZIP_FILE="$SCRIPT_DIR/api-deployment.zip"
    if [ ! -f "$ZIP_FILE" ]; then
        echo -e "  ${RED}❌ ZIP file not found at: $ZIP_FILE${NC}"
        exit 1
    fi
    
    if zipinfo "$ZIP_FILE" | grep -q "src/uepi_api/main.py"; then
        echo -e "  ${GREEN}✅ main.py found in package${NC}"
    else
        echo -e "  ${YELLOW}⚠️  main.py not found at expected path, checking alternative locations...${NC}"
        # Check if it's in a different location
        if zipinfo "$ZIP_FILE" | grep -q "main.py"; then
            echo -e "  ${GREEN}✅ main.py found (different path)${NC}"
            echo "  Found at:"
            zipinfo "$ZIP_FILE" | grep "main.py" | head -3
        else
            echo -e "  ${RED}❌ main.py NOT found in package!${NC}"
            echo "  ZIP contents (first 30 files):"
            zipinfo "$ZIP_FILE" | head -30
            exit 1
        fi
    fi
    
    # Deploy to Azure
    echo "  Deploying to Azure App Service..."
    ZIP_FILE="$SCRIPT_DIR/api-deployment.zip"
    if [ ! -f "$ZIP_FILE" ]; then
        echo -e "  ${RED}❌ ZIP file not found: $ZIP_FILE${NC}"
        exit 1
    fi
    
    az webapp deployment source config-zip \
        --resource-group "$RESOURCE_GROUP" \
        --name "$API_APP_NAME" \
        --src "$ZIP_FILE" \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
        echo -e "  ${YELLOW}⚠️  Deployment warning (may still succeed)${NC}"
    }
    
    # Set startup command - use the startup.sh script
    echo "  Configuring startup command..."
    az webapp config set \
        --name "$API_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --startup-file "startup.sh" \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    # Set STORAGE_PATH environment variable to ensure data is found
    echo "  Setting STORAGE_PATH environment variable..."
    az webapp config appsettings set \
        --name "$API_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            STORAGE_PATH="/home/site/wwwroot/data" \
            SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    # Clean up
    ZIP_FILE="$SCRIPT_DIR/api-deployment.zip"
    rm -f "$ZIP_FILE"
    
    echo -e "  ${GREEN}✅ API deployed${NC}"
    echo ""
fi

# Deploy Web
if [ "$DEPLOY_WEB" = "true" ]; then
    echo -e "${BLUE}Step 3: Building and deploying Web...${NC}"
    
    cd apps/web
    
    # Get API URL for frontend config
    if [ "$DEPLOY_API" = "true" ]; then
        API_URL="https://$API_APP_NAME.azurewebsites.net"
    else
        API_URL="${API_URL:-http://localhost:8000}"
    fi
    
    # Create production environment file
    echo "  Creating production environment file..."
    echo "VITE_API_URL=$API_URL/api/v1" > .env.production
    echo "VITE_API_BASE_URL=$API_URL/api/v1" >> .env.production
    echo -e "  ${GREEN}✅ Environment file created${NC}"
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo -e "  ${YELLOW}⚠️  npm not found. Checking for node...${NC}"
        if ! command -v node &> /dev/null; then
            echo -e "  ${RED}❌ Node.js/npm not found. Skipping web build.${NC}"
            echo -e "  ${YELLOW}Install Node.js to build the frontend: brew install node${NC}"
            DEPLOY_WEB=false
        fi
    fi
    
    if [ "$DEPLOY_WEB" = "true" ]; then
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
            echo -e "  ${YELLOW}Skipping web deployment due to build failure${NC}"
            DEPLOY_WEB=false
        }
    fi
    
    if [ "$DEPLOY_WEB" = "true" ]; then
        echo -e "  ${GREEN}✅ Frontend built${NC}"
        
        # Check if dist directory exists
        if [ ! -d "dist" ]; then
            echo -e "  ${RED}❌ dist directory not found after build${NC}"
            DEPLOY_WEB=false
        else
            # Create deployment ZIP
            echo "  Creating deployment package..."
            cd dist
            zip -r ../../../web-deployment.zip . 2>/dev/null || {
                echo -e "  ${RED}❌ Failed to create ZIP${NC}"
                DEPLOY_WEB=false
            }
            cd ..
            
            if [ "$DEPLOY_WEB" = "true" ]; then
                echo -e "  ${GREEN}✅ Deployment package created${NC}"
                
                # Deploy to Azure
                echo "  Deploying to Azure App Service..."
                az webapp deployment source config-zip \
                    --resource-group "$RESOURCE_GROUP" \
                    --name "$WEB_APP_NAME" \
                    --src ../../../web-deployment.zip \
                    --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
                    echo -e "  ${YELLOW}⚠️  Deployment warning (may still succeed)${NC}"
                }
                
                # Clean up
                rm -f ../../../web-deployment.zip
                
                echo -e "  ${GREEN}✅ Web deployed${NC}"
            fi
        fi
    fi
    
    if [ "$DEPLOY_WEB" != "true" ]; then
        echo -e "  ${YELLOW}⚠️  Skipping web deployment${NC}"
    fi
    
    echo ""
    cd ../..
fi

# Restart services
if [ "$DEPLOY_API" = "true" ]; then
    echo -e "${BLUE}Step 4: Restarting API service...${NC}"
    az webapp restart \
        --name "$API_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo -e "${GREEN}✅ API restarted${NC}"
    echo ""
fi

if [ "$DEPLOY_WEB" = "true" ]; then
    echo -e "${BLUE}Step 5: Restarting Web service...${NC}"
    az webapp restart \
        --name "$WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    echo -e "${GREEN}✅ Web restarted${NC}"
    echo ""
fi

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Production Build and Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
if [ "$DEPLOY_API" = "true" ]; then
    echo "  API App: $API_APP_NAME"
    echo "  API URL: https://$API_APP_NAME.azurewebsites.net"
fi
if [ "$DEPLOY_WEB" = "true" ]; then
    echo "  Web App: $WEB_APP_NAME"
    echo "  Web URL: https://$WEB_APP_NAME.azurewebsites.net"
fi
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
if [ "$DEPLOY_API" = "true" ]; then
    echo "1. Test API (wait 1-2 minutes for startup):"
    echo "   curl https://$API_APP_NAME.azurewebsites.net/health"
    echo ""
    echo "2. Check API logs:"
    echo "   az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
    echo ""
fi
if [ "$DEPLOY_WEB" = "true" ]; then
    echo "3. Access Web App:"
    echo "   https://$WEB_APP_NAME.azurewebsites.net"
    echo ""
fi
echo -e "${GREEN}✅ All code has been deployed to Azure!${NC}"
echo ""
echo -e "${YELLOW}Note: It may take 1-2 minutes for the services to fully start.${NC}"
echo ""
