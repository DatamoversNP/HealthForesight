#!/bin/bash
# Simple script to find ACR name

RESOURCE_GROUP="healthforesight-rg"

echo "Finding ACR in resource group: $RESOURCE_GROUP"
echo ""

# Try multiple methods
ACR_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>&1 | grep -v -i "warn\|error\|http\|notopenssl" | grep -E "^[a-z0-9]+$" | head -1)

if [ -z "$ACR_NAME" ] || [ "$ACR_NAME" == "null" ]; then
    echo "Method 1 failed. Trying all ACRs..."
    az acr list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>&1 | grep -v -i "warn\|error\|http\|notopenssl" | grep -E "^[a-z0-9]+$"
    echo ""
    echo "Please manually set ACR_NAME in the fix script, or run:"
    echo "  az acr list --resource-group $RESOURCE_GROUP --query '[].name' -o table"
else
    echo "✅ Found ACR: $ACR_NAME"
    echo ""
    echo "Use this in the fix script:"
    echo "  ACR_NAME=\"$ACR_NAME\""
fi
