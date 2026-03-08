#!/bin/bash
# Check app status and stream logs

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"
PLAN_NAME="healthforesight-plan"

echo "=== Checking App Service Status ==="
echo ""

# Check tier
echo "1. Checking App Service Plan tier..."
TIER=$(az appservice plan show \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "sku.name" -o tsv 2>/dev/null || echo "unknown")

echo "   Tier: $TIER"
echo ""

# Check app state
echo "2. Checking app state..."
APP_STATE=$(az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state -o tsv 2>/dev/null || echo "unknown")

echo "   State: $APP_STATE"
echo ""

# If stopped or quota issue, try to start
if [ "$APP_STATE" != "Running" ]; then
    echo "3. App is not running. Checking tier..."
    
    if [ "$TIER" = "F1" ] || [ "$TIER" = "FREE" ]; then
        echo "   ⚠️  Free tier detected. Upgrading to Basic (B1)..."
        az appservice plan update \
          --name $PLAN_NAME \
          --resource-group $RESOURCE_GROUP \
          --sku B1 \
          --output none
        echo "   ✅ Upgraded to Basic tier"
        sleep 10
    fi
    
    echo "   Starting app..."
    az webapp start \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --output none
    
    echo "   Waiting for app to start (15 seconds)..."
    sleep 15
    
    # Check status again
    APP_STATE=$(az webapp show \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --query state -o tsv 2>/dev/null || echo "unknown")
    
    echo "   New state: $APP_STATE"
    echo ""
fi

# If running, stream logs
if [ "$APP_STATE" = "Running" ]; then
    echo "4. App is running. Streaming logs..."
    echo "   (Press Ctrl+C to stop streaming)"
    echo ""
    az webapp log tail \
      --name $APP_NAME \
      --resource-group $RESOURCE_GROUP
else
    echo "4. ⚠️  App is still not running. Status: $APP_STATE"
    echo ""
    echo "   Check errors:"
    echo "   - Quota issues? Try: az appservice plan update --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku B1"
    echo "   - View in portal: https://portal.azure.com"
fi
