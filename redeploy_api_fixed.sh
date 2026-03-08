#!/bin/bash
# Re-deploy API with verified structure

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Re-deploying API with Fixed Structure ==="
echo ""

cd "$SCRIPT_DIR/apps/api"

# Verify we're in the right directory
if [ ! -f "src/uepi_api/main.py" ]; then
    echo "❌ ERROR: src/uepi_api/main.py not found!"
    echo "   Current directory: $(pwd)"
    echo "   Expected: $SCRIPT_DIR/apps/api"
    exit 1
fi

echo "✅ Verified source files in correct location"
echo ""

# Generate requirements.txt
echo "1. Generating requirements.txt..."
if command -v poetry &> /dev/null; then
    poetry export -f requirements.txt --output requirements.txt --without-hashes 2>/dev/null || {
        echo "   Creating fallback requirements.txt..."
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
    }
else
    echo "   Poetry not found, creating basic requirements.txt..."
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
fi

echo "   ✅ requirements.txt ready"
echo ""

# Create startup.sh
echo "2. Creating startup.sh..."
cat > startup.sh <<'EOF'
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
EOF
chmod +x startup.sh
echo "   ✅ startup.sh created"
echo ""

# Create .deployment
cat > .deployment <<EOF
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
EOF

# Create ZIP
echo "3. Creating deployment ZIP..."
zip -r deploy.zip . \
  -x "*.git*" \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.log" \
  -x "*.pytest_cache*" \
  -x "*.mypy_cache*" \
  -x "deploy.zip" \
  -x "data/*" \
  -x "target_data_model/*" \
  -x "tests/*" \
  -x "scripts/*" \
  2>&1 | grep -v "adding:" | head -5

# Verify ZIP
echo ""
echo "4. Verifying ZIP structure..."
if zipinfo deploy.zip | grep -q "src/uepi_api/main.py"; then
    echo "   ✅ src/uepi_api/main.py found in ZIP"
else
    echo "   ❌ ERROR: src/uepi_api/main.py NOT found in ZIP!"
    echo "   ZIP contents:"
    zipinfo deploy.zip | grep "src/" | head -10
    exit 1
fi

if zipinfo deploy.zip | grep -q "requirements.txt"; then
    echo "   ✅ requirements.txt found in ZIP"
else
    echo "   ❌ ERROR: requirements.txt NOT found in ZIP!"
    exit 1
fi

echo "   ✅ ZIP structure verified"
echo ""

# Deploy
echo "5. Deploying to Azure..."
echo "   ⏳ This may take 2-5 minutes (uploading ZIP and installing dependencies)..."
echo ""

# Deploy with timeout and progress indication
DEPLOY_OUTPUT=$(az webapp deploy \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src-path deploy.zip \
  --type zip \
  --timeout 600 \
  2>&1)

if echo "$DEPLOY_OUTPUT" | grep -v "NotOpenSSLWarning" | grep -q "Deployment successful\|Successfully deployed"; then
    echo "   ✅ Deployment completed successfully"
elif echo "$DEPLOY_OUTPUT" | grep -v "NotOpenSSLWarning" | grep -q "Accepted\|202"; then
    echo "   ⏳ Deployment accepted - building in background..."
    echo "   This may take 2-5 minutes. Checking status..."
    
    # Try legacy method if new one doesn't work
    echo "   Trying alternative deployment method..."
    az webapp deployment source config-zip \
      --resource-group $RESOURCE_GROUP \
      --name $APP_NAME \
      --src deploy.zip \
      --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
    
    echo "   ✅ Deployment initiated"
else
    echo "   ⚠️  Deployment may have issues. Check output above."
    echo "   Continuing anyway..."
fi

echo ""

# Clean up
rm -f deploy.zip

# Set PYTHONPATH and startup command
echo "6. Configuring app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App configured"
echo ""

# Restart
echo "7. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none

echo "   ✅ App restarted"
echo ""

echo "Waiting 20 seconds for deployment to complete..."
sleep 20

echo ""
echo "=== Testing ==="
echo "Testing health endpoint..."
curl -s https://$APP_NAME.azurewebsites.net/health | head -10

echo ""
echo ""
echo "Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
