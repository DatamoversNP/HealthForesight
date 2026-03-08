#!/bin/bash
# Get the ACTUAL container logs to see what's happening

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Getting Real Container Logs ==="
echo ""

echo "Streaming logs for 30 seconds to see container startup..."
echo "Look for [STARTUP] messages or error messages..."
echo ""
echo "--- START OF LOG STREAM ---"
timeout 30 az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP 2>&1 | grep -v "NotOpenSSLWarning" | grep -v "Welcome, you are now connected" || true
echo "--- END OF LOG STREAM ---"
echo ""

echo ""
echo "Checking latest Docker log file via Kudu API..."
echo ""
# Try to get the latest docker log
DOCKER_LOG_URL="https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker"
curl -s "$DOCKER_LOG_URL" 2>/dev/null | tail -100 | grep -E "STARTUP|Container|Error|Failed|Traceback|Exception|uvicorn|Application|ModuleNotFound" || {
    echo "  Could not access Docker logs via API"
    echo ""
    echo "Manual check required:"
    echo "  1. Go to: https://${APP_NAME}.scm.azurewebsites.net"
    echo "  2. Navigate to: Debug console → CMD"
    echo "  3. Go to: /home/LogFiles"
    echo "  4. Look for: 2026_01_19_*_docker.log"
    echo "  5. Open the latest file and search for 'STARTUP' or errors"
}
