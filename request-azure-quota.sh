#!/bin/bash
# Request Azure Quota Increase

echo "📋 Azure Quota Increase Request Helper"
echo "======================================"
echo ""

# Check if logged in
if ! az account show &>/dev/null; then
    echo "⚠️  Not logged in to Azure"
    echo "   Run: az login"
    exit 1
fi

# Get subscription info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
LOCATION="${1:-eastus}"

echo "Subscription: $SUBSCRIPTION_NAME"
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Region: $LOCATION"
echo ""

# Check current quota
echo "📊 Checking current quota..."
az vm list-usage \
  --location $LOCATION \
  --output table

echo ""
echo "📝 To request quota increase:"
echo ""
echo "1. Go to Azure Portal:"
echo "   https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade"
echo ""
echo "2. Click 'New support request'"
echo ""
echo "3. Fill in:"
echo "   - Issue type: Service and subscription limits (quotas)"
echo "   - Subscription: $SUBSCRIPTION_NAME"
echo "   - Quota type: Compute-VM (cores-v3) family"
echo "   - Region: $LOCATION"
echo "   - New limit: 2 cores (for Basic tier)"
echo ""
echo "4. Or use direct link:"
echo "   https://portal.azure.com/#view/Microsoft_Azure_Support/NewSupportRequestV3Blade/~/supportRequestDetails"
echo ""
echo "💡 Alternative: Try a different region with available quota"
echo "   ./request-azure-quota.sh westus2"
echo ""


