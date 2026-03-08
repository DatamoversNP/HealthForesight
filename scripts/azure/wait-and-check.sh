#!/bin/bash
# Wait and check if API is responding

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Waiting 30 seconds for app to fully start..."
sleep 30

echo ""
echo "Testing API health endpoint..."
API_URL="https://$API_APP_NAME.azurewebsites.net"

for i in {1..5}; do
    echo "Attempt $i/5..."
    if curl -f -s -m 10 "$API_URL/api/v1/health" > /dev/null 2>&1; then
        echo "✅ API is responding!"
        echo "API URL: $API_URL"
        echo "API Docs: $API_URL/docs"
        exit 0
    else
        echo "⏳ Not responding yet, waiting 10 seconds..."
        sleep 10
    fi
done

echo ""
echo "❌ API is not responding after 5 attempts"
echo ""
echo "Please check Azure Portal Log Stream for errors:"
echo "  https://portal.azure.com/#@/resource/subscriptions/.../providers/Microsoft.Web/sites/$API_APP_NAME/logStream"
echo ""
echo "Or run:"
echo "  az webapp log tail --resource-group $RESOURCE_GROUP --name $API_APP_NAME"

