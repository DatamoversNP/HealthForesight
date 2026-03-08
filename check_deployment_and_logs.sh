#!/bin/bash
# Check deployment status and get logs via different methods

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Deployment Status ==="
echo ""

echo "1. Checking recent deployments..."
az webapp deployment list \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0:3].{Status:status,Time:active_time,Message:message}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"

echo ""
echo "2. Checking container status..."
az webapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{state:state,defaultHostName:defaultHostName,linuxFxVersion:siteConfig.linuxFxVersion}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"

echo ""
echo "3. Checking if container is running via Kudu (SCM site)..."
# Try to get container info via Kudu API
SCM_URL="https://${APP_NAME}.scm.azurewebsites.net"
echo "   SCM URL: $SCM_URL"
echo "   Try accessing: $SCM_URL/api/logs/docker"
echo ""

echo "4. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ App is working!"
    curl -s https://$APP_NAME.azurewebsites.net/health | head -5
elif [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
    echo "   ⚠️  Container might still be starting"
    echo "   Wait 1-2 more minutes"
else
    echo "   ⚠️  App not responding (HTTP $HTTP_CODE)"
fi

echo ""
echo "=== Manual Checks ==="
echo ""
echo "If logs still don't show, try these:"
echo ""
echo "1. Azure Portal -> App Service -> Deployment Center"
echo "   Check if the container deployment shows any errors"
echo ""
echo "2. Azure Portal -> App Service -> Log stream"
echo "   Enable if not already enabled"
echo ""
echo "3. Azure Portal -> App Service -> SSH (if available)"
echo "   Connect and check: docker ps, docker logs"
echo ""
echo "4. Check SCM site directly:"
echo "   https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker"
