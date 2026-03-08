#!/bin/bash
# IMMEDIATELY STOP APP TO SAVE COSTS

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "⚠️  STOPPING APP TO SAVE COSTS ⚠️"
echo ""

az webapp stop \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "✅ App stopped - costs paused"
echo ""
echo "You can fix deployment when ready. Costs are now minimal."
