#!/bin/bash
# Cleanup failed Azure resources and retry migration

set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"

echo "Cleaning up existing resources..."

# Check if resource group exists
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo "Deleting resource group: $RESOURCE_GROUP"
    az group delete --name $RESOURCE_GROUP --yes --no-wait
    echo "Resource group deletion initiated. Waiting 30 seconds..."
    sleep 30
else
    echo "Resource group does not exist. Proceeding..."
fi

echo ""
echo "Now run the migration script again:"
echo "./scripts/azure/migrate-to-azure.sh"

