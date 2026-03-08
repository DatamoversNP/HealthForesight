#!/bin/bash
# Request App Service Plan Quota Increase

echo "📋 App Service Plan Quota Request"
echo "=================================="
echo ""

# Check if logged in
if ! az account show &>/dev/null; then
    echo "⚠️  Not logged in to Azure"
    echo "   Run: az login"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
LOCATION="${1:-eastus}"

echo "Subscription: $SUBSCRIPTION_NAME"
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Region: $LOCATION"
echo ""

echo "📝 App Service Plan quotas are managed differently than VM quotas."
echo ""
echo "To request App Service Plan quota increase:"
echo ""
echo "Method 1: Via Support Request (Recommended)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Go to Azure Portal:"
echo "   https://portal.azure.com"
echo ""
echo "2. Search for 'Help + support' in the top search bar"
echo ""
echo "3. Click 'New support request'"
echo ""
echo "4. Fill in the form:"
echo "   - Problem type: Service and subscription limits (quotas)"
echo "   - Subscription: $SUBSCRIPTION_NAME"
echo "   - Quota type: Select 'App Service Plan' or 'Compute'"
echo "   - Region: $LOCATION"
echo "   - Description: 'Request quota increase for App Service Plan Basic tier. Need 1 core for Basic B1 plan.'"
echo ""
echo "5. Click 'Review + create'"
echo ""
echo "Direct link to create support request:"
echo "   https://portal.azure.com/#view/Microsoft_Azure_Support/NewSupportRequestV3Blade"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Method 2: Try Creating App Service Plan Directly"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Sometimes the quota is available but not shown. Try creating the plan:"
echo ""
echo "  az appservice plan create \\"
echo "    --name test-plan \\"
echo "    --resource-group <your-rg> \\"
echo "    --location $LOCATION \\"
echo "    --sku B1"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Method 3: Use Free/Consumption Tier (No Quota Needed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Deploy using services that don't require quota:"
echo "  - Azure Static Web Apps (Free tier)"
echo "  - Azure Functions (Consumption plan)"
echo "  - Azure Container Apps (Consumption plan)"
echo ""
echo "Run: ./deploy-to-azure-free-tier.sh"
echo ""


