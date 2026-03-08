#!/bin/bash
# Enable detailed logging and check container startup

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Enabling Detailed Logging ==="
echo ""

# Step 1: Enable application logging
echo "1. Enabling application logging (Filesystem)..."
az webapp log config \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --application-logging filesystem \
    --level verbose \
    --docker-container-logging filesystem \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ Logging enabled"
echo ""

# Step 2: Check current container startup command
echo "2. Checking container startup command..."
az webapp config container show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{image:name,command:dockerCommand}" \
    -o json 2>&1 | grep -v "NotOpenSSLWarning" | jq '.' || {
    echo "  ⚠️  Could not get container config"
}
echo ""

# Step 3: Verify PORT is set
echo "3. Verifying environment variables..."
az webapp config appsettings list \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='PORT' || name=='WEBSITES_PORT' || name=='PYTHONPATH'].{Name:name,Value:value}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"
echo ""

# Step 4: Restart app to apply logging
echo "4. Restarting app to apply logging..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true
echo "  ✅ App restarted"
echo ""

echo "=== Waiting 30 seconds for startup ==="
sleep 30

# Step 5: Try to get logs
echo ""
echo "5. Attempting to get container logs..."
echo "   Run this to see live logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""

# Try direct log fetch
echo "   Fetching recent logs..."
az webapp log tail \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP 2>&1 | grep -v "NotOpenSSLWarning" | head -30 || {
    echo "   ⚠️  Could not fetch logs (app might be stopped)"
}

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Check Azure Portal -> App Service -> Log stream"
echo "   Enable if not already enabled"
echo ""
echo "2. Try SSH access:"
echo "   Azure Portal -> App Service -> SSH"
echo "   Then run: docker ps -a"
echo "   Then: docker logs <container_id>"
echo ""
echo "3. Check if the issue is with the startup command:"
echo "   The Dockerfile uses: uvicorn uepi_api.main:app --host 0.0.0.0 --port \${PORT:-8000}"
echo "   Make sure PORT environment variable is set to 8000"
