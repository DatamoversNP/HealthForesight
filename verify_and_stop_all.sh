#!/bin/bash
# Verify and stop all Azure services

RESOURCE_GROUP="healthforesight-rg"
APP_NAME="hf-api8755146"

echo "=== VERIFYING AND STOPPING ALL SERVICES ==="
echo ""

# Check current status
echo "Step 1: Checking current App Service status..."
STATE=$(az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "Unknown")
echo "  Current state: $STATE"
echo ""

# Stop the app if not already stopped
if [ "$STATE" != "Stopped" ]; then
    echo "Stopping App Service..."
    az webapp stop --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
    sleep 3
    STATE=$(az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "Unknown")
    echo "  ✅ App Service state: $STATE"
else
    echo "  ✅ App Service already stopped"
fi
echo ""

# Scale down App Service Plan
echo "Step 2: Scaling down App Service Plan to 0 workers..."
PLAN_NAME=$(az appservice plan list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -n "$PLAN_NAME" ] && [ "$PLAN_NAME" != "null" ]; then
    echo "  Found plan: $PLAN_NAME"
    CURRENT_WORKERS=$(az appservice plan show --name "$PLAN_NAME" --resource-group "$RESOURCE_GROUP" --query "sku.capacity" -o tsv 2>/dev/null || echo "0")
    echo "  Current workers: $CURRENT_WORKERS"
    
    if [ "$CURRENT_WORKERS" != "0" ]; then
        az appservice plan update --name "$PLAN_NAME" --resource-group "$RESOURCE_GROUP" --number-of-workers 0 >/dev/null 2>&1
        echo "  ✅ Scaled down to 0 workers"
    else
        echo "  ✅ Already at 0 workers"
    fi
else
    echo "  No App Service Plan found"
fi
echo ""

# Check SKU/tier
echo "Step 3: Checking App Service Plan tier (cost impact)..."
if [ -n "$PLAN_NAME" ] && [ "$PLAN_NAME" != "null" ]; then
    SKU=$(az appservice plan show --name "$PLAN_NAME" --resource-group "$RESOURCE_GROUP" --query "sku.name" -o tsv 2>/dev/null || echo "Unknown")
    TIER=$(az appservice plan show --name "$PLAN_NAME" --resource-group "$RESOURCE_GROUP" --query "sku.tier" -o tsv 2>/dev/null || echo "Unknown")
    echo "  Tier: $TIER"
    echo "  SKU: $SKU"
    
    if [ "$TIER" != "Free" ] && [ "$TIER" != "F1" ]; then
        echo ""
        echo "  ⚠️  WARNING: Plan is on $TIER tier, which incurs charges even when stopped!"
        echo "  Consider downgrading to Free tier to avoid costs:"
        echo "    az appservice plan update --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku FREE"
    fi
fi
echo ""

# Final verification
echo "Step 4: Final status check..."
APP_STATE=$(az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv 2>/dev/null || echo "Unknown")
echo "  App Service: $APP_STATE"

if [ -n "$PLAN_NAME" ] && [ "$PLAN_NAME" != "null" ]; then
    WORKERS=$(az appservice plan show --name "$PLAN_NAME" --resource-group "$RESOURCE_GROUP" --query "sku.capacity" -o tsv 2>/dev/null || echo "Unknown")
    echo "  App Service Plan workers: $WORKERS"
fi
echo ""

echo "=== SUMMARY ==="
if [ "$APP_STATE" = "Stopped" ]; then
    echo "✅ App Service is STOPPED"
else
    echo "⚠️  App Service state: $APP_STATE"
fi

if [ "$WORKERS" = "0" ]; then
    echo "✅ App Service Plan scaled to 0 workers"
else
    echo "⚠️  App Service Plan workers: $WORKERS"
fi
echo ""

echo "💰 COST STATUS:"
if [ "$TIER" != "Free" ] && [ "$TIER" != "F1" ]; then
    echo "  ⚠️  Plan is on $TIER tier - may still incur charges"
    echo "  Recommended: Downgrade to Free tier"
else
    echo "  ✅ Plan is on Free tier - minimal/no charges when stopped"
fi
echo ""

echo "=== Complete ==="
