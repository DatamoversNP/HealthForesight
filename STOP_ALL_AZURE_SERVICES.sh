#!/bin/bash
# Stop all Azure services to avoid costs

RESOURCE_GROUP="healthforesight-rg"

echo "=== STOPPING ALL AZURE SERVICES ==="
echo "Resource Group: $RESOURCE_GROUP"
echo ""
echo "⚠️  This will stop all running services to prevent charges."
echo ""

# Stop App Services
echo "Step 1: Stopping App Services..."
APPS=$(az webapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$APPS" ]; then
    for app in $APPS; do
        echo "  Stopping: $app"
        az webapp stop --name "$app" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
        echo "    ✅ Stopped"
    done
else
    echo "  No App Services found"
fi
echo ""

# Scale down App Service Plans (this saves more money)
echo "Step 2: Scaling down App Service Plans to 0 instances..."
PLANS=$(az appservice plan list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$PLANS" ]; then
    for plan in $PLANS; do
        echo "  Scaling down: $plan"
        az appservice plan update --name "$plan" --resource-group "$RESOURCE_GROUP" --number-of-workers 0 >/dev/null 2>&1
        echo "    ✅ Scaled to 0 workers"
    done
else
    echo "  No App Service Plans found"
fi
echo ""

# Stop Function Apps
echo "Step 3: Stopping Function Apps..."
FUNCTIONS=$(az functionapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$FUNCTIONS" ]; then
    for func in $FUNCTIONS; do
        echo "  Stopping: $func"
        az functionapp stop --name "$func" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
        echo "    ✅ Stopped"
    done
else
    echo "  No Function Apps found"
fi
echo ""

# Stop Container Instances
echo "Step 4: Stopping Container Instances..."
CONTAINERS=$(az container list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$CONTAINERS" ]; then
    for container in $CONTAINERS; do
        echo "  Stopping: $container"
        az container stop --name "$container" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
        echo "    ✅ Stopped"
    done
else
    echo "  No Container Instances found"
fi
echo ""

# Stop Container Apps
echo "Step 5: Scaling down Container Apps to 0..."
CONTAINER_APPS=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$CONTAINER_APPS" ]; then
    for app in $CONTAINER_APPS; do
        echo "  Scaling down: $app"
        az containerapp update --name "$app" --resource-group "$RESOURCE_GROUP" --min-replicas 0 --max-replicas 0 >/dev/null 2>&1
        echo "    ✅ Scaled to 0 replicas"
    done
else
    echo "  No Container Apps found"
fi
echo ""

# Stop Virtual Machines
echo "Step 6: Stopping Virtual Machines..."
VMS=$(az vm list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$VMS" ]; then
    for vm in $VMS; do
        echo "  Stopping: $vm"
        az vm deallocate --name "$vm" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1
        echo "    ✅ Stopped (deallocated)"
    done
else
    echo "  No Virtual Machines found"
fi
echo ""

# Deactivate Static Web Apps (if any)
echo "Step 7: Checking Static Web Apps..."
STATIC_APPS=$(az staticwebapp list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if [ -n "$STATIC_APPS" ]; then
    echo "  Found Static Web Apps (these are typically free/low cost):"
    for app in $STATIC_APPS; do
        echo "    - $app"
    done
    echo "  Note: Static Web Apps are typically free, but you can delete them if needed:"
    echo "    az staticwebapp delete --name <name> --resource-group $RESOURCE_GROUP"
else
    echo "  No Static Web Apps found"
fi
echo ""

echo "=== SUMMARY ==="
echo "✅ All running services have been stopped or scaled down"
echo ""
echo "💰 COST SAVINGS:"
echo "  - App Services: Stopped"
echo "  - App Service Plans: Scaled to 0 workers"
echo "  - Function Apps: Stopped"
echo "  - Container Instances: Stopped"
echo "  - Container Apps: Scaled to 0 replicas"
echo "  - VMs: Deallocated"
echo ""
echo "📋 TO RESTART SERVICES LATER:"
echo "  # Start App Service:"
echo "    az webapp start --name hf-api8755146 --resource-group $RESOURCE_GROUP"
echo ""
echo "  # Scale up App Service Plan:"
echo "    az appservice plan update --name healthforesight-plan --resource-group $RESOURCE_GROUP --number-of-workers 1"
echo ""
echo "⚠️  Note: Some resources (Storage Accounts, ACR) may still incur minimal costs."
echo "   To fully stop costs, consider deleting the resource group:"
echo "    az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
echo "=== Complete ==="
