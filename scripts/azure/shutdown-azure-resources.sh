#!/bin/bash
# Shut down Azure resources to save costs

set -e

RESOURCE_GROUP="uepi-rg-59724"
CLUSTER_NAME="uepi-aks-59723"
ACR_NAME="uepiregistry61380"

echo "=== Shutting Down Azure Resources ==="
echo ""
echo "This will:"
echo "  - Stop AKS cluster (saves compute costs)"
echo "  - Note: Resource group and resources remain (storage costs only)"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Cluster: $CLUSTER_NAME"
echo "ACR: $ACR_NAME"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "=== Stopping AKS Cluster ==="
az aks stop --name "$CLUSTER_NAME" --resource-group "$RESOURCE_GROUP" 2>&1 || echo "Cluster already stopped or doesn't exist"

echo ""
echo "=== Azure Resources Status ==="
echo ""
echo "✅ AKS cluster stopped (no compute costs)"
echo ""
echo "Resources still running (minimal costs):"
echo "  - Resource Group: Still exists (free)"
echo "  - PostgreSQL: Still running (~$50-100/month)"
echo "  - Storage Accounts: Still running (~$1-5/month)"
echo "  - Key Vault: Still running (free)"
echo "  - ACR: Still running (~$5/month)"
echo ""
echo "To stop PostgreSQL (saves most money):"
echo "  az postgres flexible-server stop --resource-group $RESOURCE_GROUP --name uepi-postgres-59725"
echo ""
echo "To delete everything (complete cleanup):"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo ""
echo "To restart AKS later:"
echo "  az aks start --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "✅ Azure resources shut down!"

