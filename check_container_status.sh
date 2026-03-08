#!/bin/bash
# Check container status and logs

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Container Status ==="
echo ""

echo "1. Container configuration:"
az webapp config show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "linuxFxVersion" -o tsv 2>&1 | grep -v "NotOpenSSLWarning"

echo ""
echo "2. App state:"
az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "state" -o tsv 2>&1 | grep -v "NotOpenSSLWarning"

echo ""
echo "3. Streaming logs (last 30 lines):"
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  2>&1 | grep -v "NotOpenSSLWarning" | tail -30
