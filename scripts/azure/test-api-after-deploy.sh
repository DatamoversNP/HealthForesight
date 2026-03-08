#!/bin/bash
# Test API after deployment

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Waiting for deployment to complete..."
echo "This may take 2-3 minutes..."
echo ""

# Wait a bit for the app to start
sleep 30

echo "Checking API status..."
echo ""

# Check app state
echo "1. App Service State:"
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --query "{state:state, defaultHostName:defaultHostName}" \
  --output table

echo ""
echo "2. Testing API Health Endpoint:"
API_URL="https://$API_APP_NAME.azurewebsites.net"
HEALTH_URL="$API_URL/api/v1/health"

for i in {1..10}; do
    echo "   Attempt $i: Testing $HEALTH_URL..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$HEALTH_URL" 2>&1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo ""
        echo "✅ API is responding!"
        echo "   HTTP Status: $HTTP_CODE"
        echo ""
        echo "Response:"
        curl -s -m 5 "$HEALTH_URL" | head -5
        echo ""
        echo "API URL: $API_URL"
        echo "API Docs: $API_URL/docs"
        exit 0
    elif [ "$HTTP_CODE" = "000" ]; then
        echo "   ⏳ Connection failed (app may still be starting)..."
    else
        echo "   ⚠️  HTTP $HTTP_CODE (app may still be starting)..."
    fi
    
    if [ $i -lt 10 ]; then
        echo "   Waiting 15 seconds before next attempt..."
        sleep 15
    fi
done

echo ""
echo "⏳ API is not responding yet."
echo ""
echo "Check logs in Azure Portal:"
echo "  https://portal.azure.com -> App Services -> $API_APP_NAME -> Log stream"
echo ""
echo "Or download logs:"
echo "  az webapp log download --resource-group $RESOURCE_GROUP --name $API_APP_NAME --log-file api-logs.zip"

