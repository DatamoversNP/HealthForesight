#!/bin/bash
# Test API health endpoint

API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"
API_URL="https://$API_APP_NAME.azurewebsites.net"

echo "Testing API health endpoint..."
echo "URL: $API_URL/api/v1/health"
echo ""

for i in {1..5}; do
    echo "Attempt $i/5..."
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -m 10 "$API_URL/api/v1/health" 2>&1)
    http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS/d')
    
    if [ "$http_status" = "200" ]; then
        echo "✅ API is responding!"
        echo "Response: $body"
        echo ""
        echo "API URL: $API_URL"
        echo "API Docs: $API_URL/docs"
        exit 0
    elif [ -n "$http_status" ]; then
        echo "HTTP Status: $http_status"
        echo "Response: $body"
    else
        echo "Connection failed or timeout"
    fi
    
    if [ $i -lt 5 ]; then
        echo "Waiting 10 seconds before retry..."
        sleep 10
    fi
done

echo ""
echo "❌ API is not responding after 5 attempts"
echo ""
echo "Check Azure Portal Log Stream for detailed errors:"
echo "  https://portal.azure.com/#@/resource/subscriptions/.../providers/Microsoft.Web/sites/$API_APP_NAME/logStream"

