#!/bin/bash
# Verify Azure Deployment

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"

echo "Verifying Azure Deployment..."
echo ""

# Check API health
echo "1. Checking API Health..."
API_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s "$API_URL/api/v1/health" > /dev/null; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
fi

# Check App Service status
echo ""
echo "2. Checking App Service Status..."
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, defaultHostName:defaultHostName}" \
  --output table

# Check Static Web App status
echo ""
echo "3. Checking Static Web App Status..."
az staticwebapp show \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{defaultHostname:defaultHostname, provisioningState:provisioningState}" \
  --output table

# Check storage account
echo ""
echo "4. Checking Storage Account..."
STORAGE_ACCOUNT=$(az storage account list \
  --resource-group $RESOURCE_GROUP \
  --query "[0].name" -o tsv)

if [ -n "$STORAGE_ACCOUNT" ]; then
    echo "✅ Storage Account: $STORAGE_ACCOUNT"
    
    # List file shares
    echo ""
    echo "5. Checking File Shares..."
    az storage share list \
      --account-name $STORAGE_ACCOUNT \
      --query "[].{Name:name, Quota:properties.quota}" \
      --output table
else
    echo "❌ No storage account found"
fi

echo ""
echo "Verification completed!"
