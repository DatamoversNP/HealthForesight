#!/bin/bash
# Deploy API to Azure App Service

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"

echo "Deploying API to Azure App Service..."

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Set app settings BEFORE zip deploy so Oryx runs when we push (installs requirements.txt)
echo "Setting app settings so Oryx build runs during deploy..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>/dev/null || true
# Remove Run From Package so Oryx can run (they are incompatible)
az webapp config appsettings delete \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --setting-names WEBSITE_RUN_FROM_PACKAGE \
  --output none 2>/dev/null || true

# Set startup command (script name relative to wwwroot)
echo "Setting startup command to startup.sh..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --startup-file "startup.sh" \
  --output none 2>/dev/null || true

# Create deployment package from project root to include packages/common
echo "Creating deployment package (including packages/common)..."
# Create startup.sh script
echo "Creating startup.sh script..."
"$SCRIPT_DIR/create-startup-script.sh" || {
    # Fallback: create startup.sh directly
    cat > apps/api/startup.sh << 'EOF'
#!/bin/bash
# Startup script for Azure App Service
cd /home/site/wwwroot
UEPI_DIR=$(find . -maxdepth 3 -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname)
COMMON_DIR=$(find . -maxdepth 3 -type d -path "*/packages/common/src" 2>/dev/null | head -1)
if [ -n "$UEPI_DIR" ] && [ -d "$UEPI_DIR/uepi_api" ]; then
    export PYTHONPATH="$UEPI_DIR:${COMMON_DIR}:$PYTHONPATH"
    cd "$UEPI_DIR"
elif [ -d "src/uepi_api" ]; then
    export PYTHONPATH="/home/site/wwwroot/src:${COMMON_DIR}:$PYTHONPATH"
    cd src
else
    export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
    cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot
fi
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    exec /home/site/wwwroot/antenv/bin/python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
elif [ -f "/home/site/wwwroot/antenv/bin/python3" ]; then
    exec /home/site/wwwroot/antenv/bin/python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
else
    python3 -m pip install --user -r requirements.txt > /tmp/pip-install.log 2>&1 || true
    exec python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
fi
EOF
    chmod +x apps/api/startup.sh
}

# Create a temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy apps/api to temp directory
echo "Copying apps/api..."
cp -r apps/api/* "$TEMP_DIR/"

# Ensure startup.sh exists and is executable (copy from apps/api if it exists)
if [ -f "apps/api/startup.sh" ]; then
    cp apps/api/startup.sh "$TEMP_DIR/startup.sh"
    chmod +x "$TEMP_DIR/startup.sh"
    echo "✅ startup.sh copied to deployment package"
else
    echo "⚠️  startup.sh not found in apps/api/, creating basic one..."
    cat > "$TEMP_DIR/startup.sh" << 'EOF'
#!/bin/bash
cd /home/site/wwwroot
UEPI_DIR=$(find . -maxdepth 3 -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname)
COMMON_DIR=$(find . -maxdepth 3 -type d -path "*/packages/common/src" 2>/dev/null | head -1)
if [ -n "$UEPI_DIR" ] && [ -d "$UEPI_DIR/uepi_api" ]; then
    export PYTHONPATH="$UEPI_DIR:${COMMON_DIR}:$PYTHONPATH"
    cd "$UEPI_DIR"
elif [ -d "src/uepi_api" ]; then
    export PYTHONPATH="/home/site/wwwroot/src:${COMMON_DIR}:$PYTHONPATH"
    cd src
else
    export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
    cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot
fi
if [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    exec /home/site/wwwroot/antenv/bin/python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
elif [ -f "/home/site/wwwroot/antenv/bin/python3" ]; then
    exec /home/site/wwwroot/antenv/bin/python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
else
    python3 -m pip install --user -r requirements.txt > /tmp/pip-install.log 2>&1 || true
    exec python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
fi
EOF
    chmod +x "$TEMP_DIR/startup.sh"
    echo "✅ startup.sh created in deployment package"
fi

# Copy packages/common to temp directory
echo "Copying packages/common..."
mkdir -p "$TEMP_DIR/packages/common"
cp -r packages/common/src "$TEMP_DIR/packages/common/"

# Create deployment zip from temp directory
cd "$TEMP_DIR" || exit 1
zip -r "$PROJECT_ROOT/api-deployment.zip" . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x "*.git*" \
  -x "*.env*" \
  -x "*.log" \
  -x "venv/*" \
  -x ".venv/*" \
  -x "node_modules/*" \
  -x "*.zip" \
  -x "data/*" \
  -x "src/data/*"

# Clean up temp directory
cd "$PROJECT_ROOT" || exit 1
rm -rf "$TEMP_DIR"

# Deploy to Azure (use az webapp deploy; config-zip is deprecated)
echo "Deploying to Azure (Oryx will run build now that SCM_DO_BUILD_DURING_DEPLOYMENT is set)..."
az webapp deploy \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src-path "$PROJECT_ROOT/api-deployment.zip" \
  --type zip

# Restart app
echo "Restarting app..."
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --output none

# Clean up
rm -f "$PROJECT_ROOT/api-deployment.zip"

echo ""
echo "Deployment completed!"
echo "API URL: https://$API_APP_NAME.azurewebsites.net"
echo ""
echo "Waiting 60 seconds for app to start..."
sleep 60
echo ""
echo "Testing API health endpoint..."
if curl -f -s -m 10 "https://$API_APP_NAME.azurewebsites.net/api/v1/health" > /dev/null 2>&1; then
    echo "✅ API is responding!"
else
    echo "⏳ API is still starting. Check logs:"
    echo "   az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
fi

