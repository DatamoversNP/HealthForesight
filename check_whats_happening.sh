#!/bin/bash
# Check what's actually happening with the container now

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Container Status ==="
echo ""

echo "1. App State:"
az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "{State:state, DefaultHostName:defaultHostName}" -o json 2>&1 | grep -v "NotOpenSSLWarning" || true
echo ""

echo "2. Container Configuration:"
az webapp config container show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "{Image:DOCKER_CUSTOM_IMAGE_NAME, RegistryURL:DOCKER_REGISTRY_SERVER_URL}" -o json 2>&1 | grep -v "NotOpenSSLWarning" || true
echo ""

echo "3. Recent Container Events (last 50 lines):"
echo "   Looking for: ContainerCreateFailure, [STARTUP], Traceback, Error"
echo ""
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -E "Container|STARTUP|Traceback|Error|Failed|Exception|ModuleNotFound|uvicorn|Application" | tail -50 || echo "No relevant logs found"
echo ""

echo "4. Checking if container is running..."
# Try to get container status from Kudu API
echo "   (This may take a moment)"
curl -s "https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker" 2>/dev/null | tail -30 || echo "   Could not access Docker logs via Kudu"
echo ""

echo "=== Next Steps ==="
echo ""
echo "If still failing, check Azure Portal:"
echo "  https://portal.azure.com → App Services → $APP_NAME → Log stream"
echo ""
echo "Or check Kudu console directly:"
echo "  https://${APP_NAME}.scm.azurewebsites.net"
echo "  Then navigate to: LogFiles → 2026_01_19_*_docker.log"
