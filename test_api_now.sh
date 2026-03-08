#!/bin/bash
# Quick API test

APP_NAME="hf-api8755146"

echo "=== Testing API ==="
echo ""

echo "1. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /tmp/api_response.txt -w "%{http_code}" https://${APP_NAME}.azurewebsites.net/health 2>/dev/null || echo "000")
RESPONSE=$(cat /tmp/api_response.txt 2>/dev/null || echo "")

echo "   HTTP Status: $HTTP_CODE"
echo "   Response: $RESPONSE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! API is working!"
    echo ""
    echo "Your API is live at:"
    echo "   https://${APP_NAME}.azurewebsites.net"
    echo "   https://${APP_NAME}.azurewebsites.net/health"
    echo "   https://${APP_NAME}.azurewebsites.net/docs"
else
    echo "⚠️  API is not responding correctly"
    echo ""
    echo "Checking recent container logs..."
    echo "   (This will show if container is starting or still failing)"
fi
