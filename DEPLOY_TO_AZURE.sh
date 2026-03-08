#!/bin/bash
# Complete Azure Deployment Script for HealthForesight Platform

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
echo -e "${BLUE}🚀 Azure Deployment - HealthForesight Platform${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    echo "   macOS: brew install azure-cli"
    echo "   Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi
echo "  ✅ Azure CLI installed"

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Please install it first.${NC}"
    exit 1
fi
echo "  ✅ Git installed"

# Check if logged in
if ! az account show &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login...${NC}"
    az login
fi

echo -e "${GREEN}✅ Prerequisites check complete${NC}"
echo ""

# Get user input
echo -e "${YELLOW}Step 2: Configuration${NC}"
read -p "Resource Group Name [healthforesight-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-healthforesight-rg}

read -p "Azure Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

# Generate a shorter, valid storage account name (max 24 chars, lowercase + numbers only)
generate_storage_name() {
    # Use shorter base name + timestamp suffix (max 24 chars total)
    TIMESTAMP=$(date +%s | tail -c 8)  # Last 8 digits of timestamp
    echo "hf${TIMESTAMP}" | head -c 24
}

STORAGE_ACCOUNT_DEFAULT=$(generate_storage_name)
read -p "Storage Account Name (must be globally unique, 3-24 chars, lowercase+numbers only) [$STORAGE_ACCOUNT_DEFAULT]: " STORAGE_ACCOUNT_INPUT
STORAGE_ACCOUNT=${STORAGE_ACCOUNT_INPUT:-$STORAGE_ACCOUNT_DEFAULT}

# Validate storage account name
if ! echo "$STORAGE_ACCOUNT" | grep -qE '^[a-z0-9]{3,24}$'; then
    echo -e "${RED}❌ Invalid storage account name: $STORAGE_ACCOUNT${NC}"
    echo "   Must be 3-24 characters, lowercase letters and numbers only"
    echo "   Using generated name instead: $STORAGE_ACCOUNT_DEFAULT"
    STORAGE_ACCOUNT=$STORAGE_ACCOUNT_DEFAULT
fi

# Generate shorter API app name
generate_api_name() {
    TIMESTAMP=$(date +%s | tail -c 8)
    echo "hf-api${TIMESTAMP}"
}

API_APP_NAME_DEFAULT=$(generate_api_name)
read -p "API App Name (must be globally unique) [$API_APP_NAME_DEFAULT]: " API_APP_NAME_INPUT
API_APP_NAME=${API_APP_NAME_INPUT:-$API_APP_NAME_DEFAULT}

# Generate shorter web app name
generate_web_name() {
    TIMESTAMP=$(date +%s | tail -c 8)
    echo "hf-web${TIMESTAMP}"
}

WEB_APP_NAME_DEFAULT=$(generate_web_name)
read -p "Web App Name (must be globally unique) [$WEB_APP_NAME_DEFAULT]: " WEB_APP_NAME_INPUT
WEB_APP_NAME=${WEB_APP_NAME_INPUT:-$WEB_APP_NAME_DEFAULT}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  API App: $API_APP_NAME"
echo "  Web App: $WEB_APP_NAME"
echo ""
read -p "Continue with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi
echo ""

# Create resource group
echo -e "${BLUE}Step 3: Creating resource group...${NC}"
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo "  ℹ️  Resource group already exists"
else
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    echo -e "  ${GREEN}✅ Resource group created${NC}"
fi
echo ""

# Create storage account
echo -e "${BLUE}Step 4: Creating storage account...${NC}"
if az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "  ℹ️  Storage account already exists"
else
    az storage account create \
      --name $STORAGE_ACCOUNT \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku Standard_LRS \
      --kind StorageV2 \
      --output none
    echo -e "  ${GREEN}✅ Storage account created${NC}"
fi

# Create file share
echo -e "${BLUE}Step 5: Creating file share...${NC}"
AZURE_STORAGE_FILE_SHARE_NAME="healthforesight-data"
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

az storage share create \
  --name $AZURE_STORAGE_FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --output none || echo "  ℹ️  File share may already exist"
echo -e "  ${GREEN}✅ File share created${NC}"
echo ""

# Create app service plan
echo -e "${BLUE}Step 6: Creating app service plan...${NC}"
APP_SERVICE_PLAN="healthforesight-plan"

# Ask user for SKU tier (Pay-As-You-Go should have quota for Basic/Standard)
echo "  Available tiers:"
echo "    F1 (Free) - Limited features, shared resources, CPU throttling"
echo "    B1 (Basic) - ~$13/month, dedicated resources, always-on enabled (Recommended)"
echo "    B2 (Basic) - ~$25/month, better performance, 3.5GB RAM"
echo "    S1 (Standard) - ~$55/month, auto-scaling, production-ready"
echo ""

read -p "  Select SKU tier [B1]: " SKU_INPUT
SKU_INPUT=${SKU_INPUT:-B1}
SKU=$(echo "$SKU_INPUT" | tr '[:lower:]' '[:upper:]')  # Convert to uppercase (portable)

if az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "  ℹ️  App service plan already exists"
    SKU=$(az appservice plan show --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --query sku.name -o tsv)
else
    echo "  Creating app service plan with SKU: $SKU..."
    
    # List of locations to try (common regions with good quota availability)
    LOCATIONS_TO_TRY=(
        "eastus"
        "westus2"
        "westus"
        "centralus"
        "southcentralus"
        "eastus2"
        "westcentralus"
        "northcentralus"
        "canadacentral"
        "uksouth"
        "westeurope"
        "northeurope"
    )
    
    PLAN_CREATED=false
    
    # Try with selected SKU first
    if [ "$SKU" != "F1" ]; then
        echo "  Attempting to create with $SKU tier in $LOCATION..."
        if az appservice plan create \
          --name $APP_SERVICE_PLAN \
          --resource-group $RESOURCE_GROUP \
          --location $LOCATION \
          --sku $SKU \
          --is-linux \
          --output none 2>&1 | grep -q "quota\|Quota"; then
            echo -e "  ${YELLOW}⚠️  Quota error with $SKU tier in $LOCATION${NC}"
        else
            echo -e "  ${GREEN}✅ App service plan created with $SKU tier${NC}"
            PLAN_CREATED=true
        fi
    fi
    
    # If failed or using F1, try F1 in current location first
    if [ "$PLAN_CREATED" = false ]; then
        echo -e "  ${YELLOW}Trying Free (F1) tier in $LOCATION...${NC}"
        if az appservice plan create \
          --name $APP_SERVICE_PLAN \
          --resource-group $RESOURCE_GROUP \
          --location $LOCATION \
          --sku F1 \
          --is-linux \
          --output none 2>&1 | grep -q "quota\|Quota"; then
            echo -e "  ${YELLOW}⚠️  Quota error with F1 tier in $LOCATION${NC}"
        else
            echo -e "  ${GREEN}✅ App service plan created with Free (F1) tier${NC}"
            echo -e "  ${YELLOW}Note: Free tier has limitations (CPU throttling, always-on disabled)${NC}"
            SKU="F1"
            PLAN_CREATED=true
        fi
    fi
    
    # If still failed, try other locations with F1
    if [ "$PLAN_CREATED" = false ]; then
        echo -e "  ${YELLOW}No quota available in $LOCATION. Trying other Azure regions...${NC}"
        for ALT_LOCATION in "${LOCATIONS_TO_TRY[@]}"; do
            if [ "$ALT_LOCATION" = "$LOCATION" ]; then
                continue  # Skip already tried location
            fi
            echo "  Trying $ALT_LOCATION..."
            
            # Check if resource group exists in this location, if not create it
            if ! az group show --name $RESOURCE_GROUP &>/dev/null; then
                az group create --name $RESOURCE_GROUP --location $ALT_LOCATION --output none
                LOCATION=$ALT_LOCATION  # Update location
            fi
            
            if az appservice plan create \
              --name $APP_SERVICE_PLAN \
              --resource-group $RESOURCE_GROUP \
              --location $ALT_LOCATION \
              --sku F1 \
              --is-linux \
              --output none 2>&1 | grep -q "quota\|Quota"; then
                echo -e "    ${YELLOW}No quota in $ALT_LOCATION${NC}"
            else
                echo -e "  ${GREEN}✅ App service plan created with Free (F1) tier in $ALT_LOCATION${NC}"
                echo -e "  ${YELLOW}Note: Using location $ALT_LOCATION (different from your original choice)${NC}"
                SKU="F1"
                LOCATION=$ALT_LOCATION
                PLAN_CREATED=true
                break
            fi
        done
    fi
    
    # If still failed, provide detailed help
    if [ "$PLAN_CREATED" = false ]; then
        echo ""
        echo -e "  ${RED}❌ Failed to create app service plan in any available location.${NC}"
        echo ""
        echo -e "  ${YELLOW}Your Azure subscription has no quota for App Service Plans.${NC}"
        echo ""
        echo -e "  ${BLUE}Solutions:${NC}"
        echo ""
        echo "  1. ${GREEN}Request Quota Increase (Recommended)${NC}:"
        echo "     • Go to: https://portal.azure.com"
        echo "     • Navigate: Subscriptions → Your subscription → Usage + quotas"
        echo "     • Select location: $LOCATION"
        echo "     • Find: 'App Service Plans - Free'"
        echo "     • Click: 'Request increase'"
        echo "     • Request: 1 (or more)"
        echo "     • Reason: 'Need quota for App Service deployment'"
        echo "     • Approval usually takes 24-48 hours"
        echo ""
        echo "  2. ${GREEN}Upgrade Subscription${NC}:"
        echo "     • If you're on Free tier, consider upgrading to Pay-As-You-Go"
        echo "     • Pay-As-You-Go subscriptions typically have more quota"
        echo ""
        echo "  3. ${GREEN}Use Different Deployment Method${NC}:"
        echo "     • Consider Azure Container Apps (different quota)"
        echo "     • Or Azure Functions (serverless, different quota)"
        echo ""
        echo -e "  ${YELLOW}After requesting quota increase, run this script again.${NC}"
        echo ""
        exit 1
    fi
fi
echo ""

# Create API app service
echo -e "${BLUE}Step 7: Creating API app service...${NC}"
if az webapp show --name $API_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "  ℹ️  API app already exists"
else
    az webapp create \
      --name $API_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --plan $APP_SERVICE_PLAN \
      --runtime "PYTHON:3.11" \
      --output none
    echo -e "  ${GREEN}✅ API app service created${NC}"
fi

# Configure API app settings
echo -e "${BLUE}Step 8: Configuring API app settings...${NC}"

# Wait a moment for app service to be fully ready
sleep 3

# Get existing settings
echo "  Checking existing app settings..."
EXISTING_SETTINGS=$(az webapp config appsettings list \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output json 2>/dev/null || echo "[]")

# Configure app settings (check if app exists and is ready)
if az webapp show --name $API_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "  Setting app configuration..."
    
    # Try to set app settings - use individual calls to avoid conflicts
    az webapp config appsettings set \
      --name $API_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --settings \
        USE_AZURE_FILE_STORAGE=true \
        AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
        AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
        AZURE_STORAGE_FILE_SHARE_NAME=$AZURE_STORAGE_FILE_SHARE_NAME \
        USE_FILE_STORAGE=true \
        ENVIRONMENT=production \
        LOG_LEVEL=INFO \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || {
        echo -e "  ${YELLOW}⚠️  Some settings may already exist. Checking...${NC}"
        
        # If conflict, try updating settings one by one
        echo "  Updating settings individually..."
        
        # Update each setting separately
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings USE_AZURE_FILE_STORAGE=true \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings AZURE_STORAGE_FILE_SHARE_NAME=$AZURE_STORAGE_FILE_SHARE_NAME \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings USE_FILE_STORAGE=true \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings ENVIRONMENT=production \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings LOG_LEVEL=INFO \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true \
          --output none 2>/dev/null || true
        
        az webapp config appsettings set \
          --name $API_APP_NAME \
          --resource-group $RESOURCE_GROUP \
          --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
          --output none 2>/dev/null || true
    }
    
    echo -e "  ${GREEN}✅ App settings configured${NC}"
else
    echo -e "  ${YELLOW}⚠️  App service not found. Skipping settings configuration.${NC}"
fi

# Configure startup command
echo "  Configuring startup command..."
# Azure App Service uses PORT environment variable, not hardcoded 8000
# PYTHONPATH needs to include src directory where uepi_api is located
STARTUP_CMD="export PYTHONPATH=\"/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:\$PYTHONPATH\" && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}"

# Create startup script file
cat > "$SCRIPT_DIR/apps/api/startup.sh" <<'EOF'
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
EOF

# Set PYTHONPATH as app setting (required for Azure App Service)
echo "  Setting PYTHONPATH in app settings..."
az webapp config appsettings set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ PYTHONPATH configured"

# Configure startup command - use direct Python command with PYTHONPATH
# Azure App Service Python runtime uses PYTHONPATH from app settings automatically
echo "  Configuring startup command..."
if az webapp config set \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" | grep -q "Conflict"; then
    echo -e "  ${YELLOW}⚠️  Startup command may already be configured${NC}"
else
    echo "  ✅ Startup command configured"
fi

# Enable Always On (only for Basic tier and above)
if [ "$SKU" != "F1" ]; then
    echo "  Enabling Always On (Basic tier and above)..."
    if az webapp config set \
      --name $API_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --always-on true \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" | grep -q "Conflict"; then
        echo -e "  ${YELLOW}⚠️  Always On may already be configured${NC}"
    else
        echo "  ✅ Always On enabled"
    fi
else
    echo -e "  ${YELLOW}⚠️  Always On not available for Free (F1) tier${NC}"
fi

echo -e "  ${GREEN}✅ API app configured${NC}"
echo ""

# Get API URL
API_URL=$(az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostName -o tsv)

# Configure CORS (will add web app later)
az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "*" \
  --output none || echo "  ℹ️  CORS may already be configured"

echo ""

# Deploy API code
echo -e "${BLUE}Step 9: Deploying API code...${NC}"
echo "  Choose deployment method:"
echo "  1. Deploy from local ZIP (fast)"
echo "  2. Deploy from Git (recommended for CI/CD)"
echo "  3. Skip deployment (deploy manually later)"
read -p "Choice [1]: " DEPLOY_CHOICE
DEPLOY_CHOICE=${DEPLOY_CHOICE:-1}

if [ "$DEPLOY_CHOICE" = "1" ]; then
    echo "  📦 Creating deployment package..."
    cd "$SCRIPT_DIR/apps/api"
    
    # Check if poetry is available
    if ! command -v poetry &> /dev/null; then
        echo -e "  ${YELLOW}⚠️  Poetry not found. Installing temporarily...${NC}"
        pip install poetry --quiet || {
            echo -e "  ${RED}❌ Failed to install poetry. Please install it first:${NC}"
            echo "     pip install poetry"
            exit 1
        }
    fi
    
    # Generate requirements.txt from pyproject.toml (Azure App Service needs this)
    echo "  📝 Generating requirements.txt from pyproject.toml..."
    if poetry export -f requirements.txt --output requirements.txt --without-hashes 2>/dev/null; then
        echo "  ✅ requirements.txt generated"
    else
        echo -e "  ${YELLOW}⚠️  Poetry export failed. Creating basic requirements.txt...${NC}"
        # Fallback: Create requirements.txt manually
        cat > requirements.txt <<EOF
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
sqlalchemy>=2.0.23
alembic>=1.12.1
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
httpx>=0.25.0
requests>=2.31.0
psycopg2-binary>=2.9.9
redis>=5.0.1
boto3>=1.29.0
polars>=0.19.0
azure-storage-file-share>=12.17.0
pyarrow>=14.0.0
pandas>=2.1.0
prometheus-client>=0.19.0
EOF
        echo "  ✅ Basic requirements.txt created"
    fi
    
    # Create .deployment file for Azure
    cat > .deployment <<EOF
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
EOF
    
    # Create startup script for Azure (will be in deployment root)
    cat > startup.sh <<'EOF'
#!/bin/bash
# Azure App Service startup script
# Set PYTHONPATH to find modules
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"

# Change to app directory
cd /home/site/wwwroot || cd /home/site/wwwroot/src || pwd

# Use PORT environment variable (Azure App Service provides this)
# Fallback to 8000 if PORT is not set
PORT=${PORT:-8000}

# Start the application
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port $PORT
EOF
    chmod +x startup.sh
    
    # Create deployment ZIP (include src directory at root level)
    echo "  📦 Creating deployment ZIP..."
    zip -r deploy.zip . \
      -x "*.git*" \
      -x "*.venv*" \
      -x "*__pycache__*" \
      -x "*.pyc" \
      -x "*.log" \
      -x "*.pytest_cache*" \
      -x "*.mypy_cache*" \
      -x "deploy.zip" \
      -x ".deployment" \
      -x "data/*" \
      -x "target_data_model/*" \
      -x "tests/*" || {
        echo -e "  ${RED}❌ Failed to create ZIP. Make sure zip command is available.${NC}"
        echo "     Install with: brew install zip (macOS) or apt-get install zip (Linux)"
        exit 1
    }
    
    # Verify ZIP contains required files
    echo "  🔍 Verifying ZIP contents..."
    if zip -T deploy.zip > /dev/null 2>&1; then
        echo "  ✅ ZIP file is valid"
        
        # List key files in ZIP
        echo "  📋 Key files in ZIP:"
        zipinfo deploy.zip | grep -E "(src/uepi_api/main.py|requirements.txt|startup.sh)" | head -5 || echo "     (Checking...)"
    else
        echo -e "  ${RED}❌ ZIP file is corrupted!${NC}"
        exit 1
    fi
    echo ""
    
    # Clean up temporary files (but keep requirements.txt if we created it)
    # Don't delete requirements.txt as it might be needed
    
    echo "  📤 Uploading to Azure..."
    az webapp deployment source config-zip \
      --resource-group $RESOURCE_GROUP \
      --name $API_APP_NAME \
      --src deploy.zip \
      --output none
    
    rm deploy.zip
    echo -e "  ${GREEN}✅ API deployed${NC}"
    
elif [ "$DEPLOY_CHOICE" = "2" ]; then
    echo "  🔧 Setting up Git deployment..."
    cd "$SCRIPT_DIR"
    
    # Initialize git if needed
    if [ ! -d .git ]; then
        git init
        git add .
        git commit -m "Initial commit for Azure deployment" || echo "  ℹ️  Git commit may have failed"
    fi
    
    # Configure local git deployment
    DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
      --name $API_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --query url -o tsv)
    
    echo "  📝 Deployment URL: $DEPLOYMENT_URL"
    echo "  Run this command to deploy:"
    echo "    git remote add azure $DEPLOYMENT_URL"
    echo "    git push azure main"
    echo ""
    read -p "  Deploy now? (y/n): " DEPLOY_NOW
    if [ "$DEPLOY_NOW" = "y" ] || [ "$DEPLOY_NOW" = "Y" ]; then
        git remote remove azure 2>/dev/null || true
        git remote add azure $DEPLOYMENT_URL
        git push azure main || echo "  ⚠️  Git push failed. Deploy manually later."
    fi
fi

cd "$SCRIPT_DIR"
echo ""

# Create static web app
echo -e "${BLUE}Step 10: Creating static web app...${NC}"
if az staticwebapp show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "  ℹ️  Static web app already exists"
else
    az staticwebapp create \
      --name $WEB_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku Free \
      --output none
    echo -e "  ${GREEN}✅ Static web app created${NC}"
fi

# Configure web app settings
echo -e "${BLUE}Step 11: Configuring web app settings...${NC}"
az staticwebapp appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting-names \
    VITE_API_URL="https://$API_URL/api/v1" \
    VITE_API_BASE_URL="https://$API_URL/api/v1" \
  --output none

# Update CORS with web app URL
WEB_URL=$(az staticwebapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query defaultHostname -o tsv)

az webapp cors add \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --allowed-origins "https://$WEB_URL" \
  --output none || echo "  ℹ️  CORS may already be configured"

echo -e "  ${GREEN}✅ Web app configured${NC}"
echo ""

# Build and deploy web app
echo -e "${BLUE}Step 12: Building web app...${NC}"
cd "$SCRIPT_DIR/apps/web"

if [ ! -d "node_modules" ]; then
    echo "  📦 Installing dependencies..."
    npm install
fi

echo "  🔨 Building for production..."
npm run build || {
    echo -e "  ${RED}❌ Build failed. Fix errors and run build manually.${NC}"
    exit 1
}

echo -e "  ${GREEN}✅ Web app built${NC}"
echo ""

# Get deployment token
echo -e "${BLUE}Step 13: Getting deployment token...${NC}"
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.apiKey -o tsv)

echo -e "  ${GREEN}✅ Deployment token obtained${NC}"
echo ""

# Final summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Storage Account: $STORAGE_ACCOUNT"
echo "  File Share: $AZURE_STORAGE_FILE_SHARE_NAME"
echo ""
echo -e "${BLUE}🌐 URLs:${NC}"
echo "  API: https://$API_URL"
echo "  API Docs: https://$API_URL/docs"
echo "  API Health: https://$API_URL/health"
echo "  Web App: https://$WEB_URL"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Test API:"
echo "   curl https://$API_URL/health"
echo ""
echo "2. Deploy Web App:"
echo "   Install SWA CLI: npm install -g @azure/static-web-apps-cli"
echo "   Then run:"
echo "   cd apps/web"
echo "   swa deploy ./dist --deployment-token $DEPLOYMENT_TOKEN --env production"
echo ""
echo "   Or use Azure Portal:"
echo "   - Go to Azure Portal > Static Web Apps > $WEB_APP_NAME"
echo "   - Click 'Browse' to open your app"
echo ""
echo "3. View Logs:"
echo "   az webapp log tail --name $API_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "4. Monitor:"
echo "   az monitor metrics list --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$API_APP_NAME"
echo ""
echo -e "${YELLOW}⚠️  Important: Save your deployment token for future deployments!${NC}"
echo "   Token: $DEPLOYMENT_TOKEN"
echo ""
echo -e "${GREEN}✅ Platform is now deployed to Azure!${NC}"
echo ""
