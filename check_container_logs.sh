#!/bin/bash
# Get actual container logs and diagnose startup issues

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Container Status and Logs ==="
echo ""

# Step 1: Check app status
echo "1. Checking app status..."
az webapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{state:state,defaultHostName:defaultHostName,linuxFxVersion:siteConfig.linuxFxVersion,alwaysOn:siteConfig.alwaysOn}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"
echo ""

# Step 2: Check container configuration
echo "2. Checking container configuration..."
az webapp config container show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{image:name,registry:registryUrl,command:dockerCommand}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"
echo ""

# Step 3: Check environment variables
echo "3. Checking environment variables..."
az webapp config appsettings list \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='PORT' || name=='PYTHONPATH' || name=='WEBSITES_PORT'].{Name:name,Value:value}" \
    -o table 2>&1 | grep -v "NotOpenSSLWarning"
echo ""

# Step 4: Get container logs via Kudu API
echo "4. Getting container logs (stdout/stderr)..."
echo "   This will show actual application output..."
echo ""

# Get publishing credentials
PUB_CREDS=$(az webapp deployment list-publishing-profiles \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0]" -o json)

USERNAME=$(echo $PUB_CREDS | jq -r '.userName')
PASSWORD=$(echo $PUB_CREDS | jq -r '.userPWD')

# Try to get Docker logs via Kudu
echo "   Fetching logs via Kudu API..."
curl -u "$USERNAME:$PASSWORD" \
    "https://${APP_NAME}.scm.azurewebsites.net/api/logs/docker" \
    2>/dev/null | tail -50 || echo "   Could not fetch Docker logs"
echo ""

# Step 5: Check if app is running
echo "5. Testing app endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")
echo "   HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
    echo "   ⚠️  App is not responding"
    echo ""
    echo "   Trying to get response body..."
    curl -s https://$APP_NAME.azurewebsites.net/health | head -10
fi
echo ""

echo "=== Manual Steps ==="
echo ""
echo "If the container is still failing, try:"
echo ""
echo "1. Azure Portal -> App Service -> Log stream"
echo "   Enable 'Application Logging (Filesystem)' if not enabled"
echo ""
echo "2. Azure Portal -> App Service -> SSH"
echo "   Connect and run: docker ps -a"
echo "   Then: docker logs <container_id>"
echo ""
echo "3. Check Deployment Center for deployment logs"
echo ""
