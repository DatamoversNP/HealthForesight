#!/bin/bash
# Check Docker container logs for errors

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Container Logs ==="
echo ""

echo "1. App state and container configuration..."
az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{state:state,linuxFxVersion:linuxFxVersion,containerImage:siteConfig.linuxFxVersion}" \
  -o table 2>&1 | grep -v "NotOpenSSLWarning"

echo ""
echo "2. Recent logs (last 50 lines)..."
echo ""
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --max-events 50 \
  2>&1 | grep -v "NotOpenSSLWarning" | tail -50

echo ""
echo "3. Looking for specific errors..."
echo ""
az webapp log download \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file /tmp/container_logs.zip \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

if [ -f /tmp/container_logs.zip ]; then
    unzip -q /tmp/container_logs.zip -d /tmp/container_logs 2>/dev/null || true
    if [ -d /tmp/container_logs ]; then
        echo "   Checking for errors:"
        grep -r -i "error\|exception\|traceback\|failed\|module" /tmp/container_logs 2>/dev/null | head -20 || echo "   No obvious errors found"
    fi
    rm -rf /tmp/container_logs /tmp/container_logs.zip 2>/dev/null || true
fi

echo ""
echo "=== Check Complete ==="
