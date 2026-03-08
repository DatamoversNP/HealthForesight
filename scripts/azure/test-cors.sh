#!/bin/bash
# Test CORS configuration

FRONTEND_ORIGIN="https://gentle-flower-01dffcd0f.2.azurestaticapps.net"
API_URL="https://healthforesight-api-9016.azurewebsites.net"

echo "Testing CORS preflight request..."
echo "Origin: $FRONTEND_ORIGIN"
echo "API: $API_URL"
echo ""

# Test OPTIONS request (preflight)
echo "1. Testing OPTIONS (preflight) request:"
response=$(curl -X OPTIONS \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -v "$API_URL/api/v1/health" 2>&1)

echo "$response" | grep -i "access-control" || echo "No CORS headers found"

echo ""
echo "2. Testing actual GET request:"
response2=$(curl -X GET \
  -H "Origin: $FRONTEND_ORIGIN" \
  -v "$API_URL/api/v1/health" 2>&1)

echo "$response2" | grep -i "access-control" || echo "No CORS headers found"

echo ""
echo "3. Checking API health:"
curl -s "$API_URL/api/v1/health" | head -1

