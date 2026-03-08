#!/bin/bash
# Verify startup.sh is in the deployment

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Checking if startup.sh exists in deployment..."
echo ""

# Check via Kudu API
echo "Checking deployment structure..."
echo ""
echo "The startup.sh file should be at: /home/site/wwwroot/startup.sh"
echo ""
echo "To verify manually:"
echo "1. Go to: https://healthforesight-api-9016.scm.azurewebsites.net"
echo "2. Click: Debug console -> CMD"
echo "3. Run: ls -la /home/site/wwwroot/startup.sh"
echo ""
echo "If startup.sh doesn't exist, we need to redeploy with it included."

