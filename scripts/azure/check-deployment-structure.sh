#!/bin/bash
# Check if the deployment structure is correct

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Checking deployment structure..."
echo ""

# Use Azure CLI to check if files exist
echo "1. Checking if main.py exists..."
az webapp ssh \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --command "ls -la /home/site/wwwroot/src/uepi_api/main.py" 2>&1 || \
echo "   (SSH not available, trying alternative method)"

echo ""
echo "2. Checking deployment package structure..."
echo "   The deployment should have:"
echo "   - /home/site/wwwroot/src/uepi_api/main.py"
echo "   - /home/site/wwwroot/src/uepi_api/ (all modules)"
echo "   - /home/site/wwwroot/packages/common/src/ (if using common package)"
echo ""
echo "3. To verify deployment, check Azure Portal:"
echo "   https://portal.azure.com -> App Services -> $API_APP_NAME -> Advanced Tools (Kudu) -> Debug console -> CMD"
echo ""
echo "   Then navigate to: site/wwwroot/src/uepi_api/"
echo "   Check if main.py exists"

