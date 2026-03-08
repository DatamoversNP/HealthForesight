#!/bin/bash
# Script to get detailed container logs and diagnose ContainerCreateFailure

set -e

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Container Logs ==="
echo ""

echo "1. Checking app state..."
az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "{State:state, Kind:kind, LinuxFxVersion:siteConfig.linuxFxVersion}" -o json 2>&1 | grep -v "NotOpenSSLWarning" || true
echo ""

echo "2. Checking Docker configuration..."
az webapp config container show --name $APP_NAME --resource-group $RESOURCE_GROUP -o json 2>&1 | grep -v "NotOpenSSLWarning" || true
echo ""

echo "3. Downloading latest Docker logs..."
# Try to download the latest Docker log file
LOG_FILE=$(az webapp log download --name $APP_NAME --resource-group $RESOURCE_GROUP --log-file docker.log 2>&1 | grep -v "NotOpenSSLWarning" || echo "")

if [ -f "docker.log" ]; then
    echo "  ✅ Log downloaded"
    echo ""
    echo "  Last 50 lines of Docker log:"
    tail -50 docker.log | grep -E "Container|Error|Failed|Traceback|Exception|STARTUP" || tail -50 docker.log
else
    echo "  ⚠️  Could not download log file"
fi

echo ""
echo "4. Checking container logs via API..."
# Get logs from the logstream API
echo "  Recent container events:"
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -E "Container|docker|STARTUP|Error|Failed" | tail -30 || echo "  No relevant logs found"
echo ""

echo "5. Testing if we can access Kudu console..."
echo "  Kudu URL: https://$APP_NAME.scm.azurewebsites.net"
echo "  Try accessing this URL in a browser to see container logs directly"
echo ""

echo "=== Next Steps ==="
echo ""
echo "If container keeps failing, try:"
echo "1. Check Azure Portal > App Service > Log stream (for real-time logs)"
echo "2. Check Azure Portal > App Service > Container settings"
echo "3. Verify the Docker image exists in ACR:"
echo "   az acr repository show-tags --name healthforesightacr12666 --repository uepi-api --output table"
echo ""
echo "4. Try accessing the container logs via Kudu:"
echo "   https://$APP_NAME.scm.azurewebsites.net/api/logs/docker"
echo ""
