#!/bin/bash
# Fix ModuleNotFoundError: No module named 'uepi_api'

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Fixing ModuleNotFoundError ==="
echo ""

# Set PYTHONPATH in app settings
echo "1. Setting PYTHONPATH in app settings..."
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

echo "   ✅ PYTHONPATH configured"
echo ""

# Update startup command to include PYTHONPATH explicitly
echo "2. Updating startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -c \"import sys; sys.path.insert(0, '/home/site/wwwroot/src'); sys.path.insert(0, '/home/site/wwwroot/packages/common/src'); import uvicorn; uvicorn.run('uepi_api.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))\"" \
  --output none

# Better approach - use startup script with proper PYTHONPATH
cat > /tmp/startup_cmd.txt << 'EOF'
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH" && cd /home/site/wwwroot && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
EOF

# Actually, let's use a simpler startup command
echo "3. Setting simplified startup command..."
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}" \
  --output none

echo "   ✅ Startup command updated"
echo ""

# Restart the app
echo "4. Restarting app..."
az webapp restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none

echo "   ✅ App restarted"
echo ""
echo "Waiting 15 seconds for app to start..."
sleep 15

echo ""
echo "=== Testing ==="
echo "Testing health endpoint..."
curl -s https://$APP_NAME.azurewebsites.net/health | head -20

echo ""
echo ""
echo "Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
