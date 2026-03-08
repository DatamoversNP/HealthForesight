#!/bin/bash
# Final fix: Stop app, fix deployment, redeploy properly

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== STEP 1: Stop App to Save Costs ==="
echo ""
az webapp stop \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "✅ App stopped"
echo ""

echo "=== STEP 2: Fix the Real Issue ==="
echo ""
echo "Problem: Oryx extracts to /tmp/XXX but PYTHONPATH doesn't include /tmp/XXX/src"
echo "Solution: Use a startup command that Python can execute directly"
echo ""

cd "$SCRIPT_DIR/apps/api"

echo "Creating a startup.sh that will definitely work..."
cat > startup.sh <<'EOF'
#!/bin/bash
# Startup script that finds Oryx extracted directory and runs uvicorn

# Find extracted directory
EXTRACTED=$(find /tmp -maxdepth 1 -type d -name "8de*" 2>/dev/null | head -1)
if [ -z "$EXTRACTED" ]; then
    # Fallback: find any /tmp dir with antenv
    EXTRACTED=$(find /tmp -maxdepth 1 -type d -exec test -d {}/antenv \; -print 2>/dev/null | head -1)
fi

if [ -n "$EXTRACTED" ] && [ -d "$EXTRACTED/src/uepi_api" ]; then
    export PYTHONPATH="$EXTRACTED/src:$EXTRACTED/packages/common/src:$PYTHONPATH"
    cd "$EXTRACTED"
else
    export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
    cd /home/site/wwwroot
fi

exec python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
EOF

chmod +x startup.sh
echo "✅ startup.sh created"
echo ""

echo "=== STEP 3: Create deployment ZIP ==="
echo ""
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
  -x "tests/*" 2>&1 | grep -v "zip warning" || true

echo "✅ ZIP created"
echo ""

echo "=== STEP 4: Set startup command ==="
echo ""
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "startup.sh" \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "✅ Startup command set"
echo ""

echo "=== STEP 5: Deploy ==="
echo ""
echo "Deploying... (this will take 5-10 minutes)"
az webapp deploy \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src-path deploy.zip \
  --type zip \
  --async true \
  --timeout 600 \
  2>&1 | grep -v "NotOpenSSLWarning" | head -30 || true

echo ""
echo "✅ Deployment submitted"
echo ""

echo "=== STEP 6: Start App ==="
echo ""
echo "Waiting 30 seconds, then starting app..."
sleep 30

az webapp start \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "✅ App started"
echo ""

echo "=== WAIT AND TEST ==="
echo ""
echo "Wait 2-3 minutes for deployment to complete, then test:"
echo "  curl https://$APP_NAME.azurewebsites.net/health"
echo ""
echo "If it works, you'll see a JSON response. If not, check logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
