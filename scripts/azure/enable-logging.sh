#!/bin/bash
# Enable detailed application logging

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Enabling detailed application logging..."
echo ""

# Enable application logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --application-logging filesystem \
  --level verbose \
  --docker-container-logging filesystem \
  --output none

echo "✅ Logging enabled"
echo ""
echo "Now restart the app and check logs:"
echo "  az webapp restart --resource-group $RESOURCE_GROUP --name $API_APP_NAME"
echo ""
echo "Then download logs:"
echo "  az webapp log download --resource-group $RESOURCE_GROUP --name $API_APP_NAME --log-file api-logs.zip"

