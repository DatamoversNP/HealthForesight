#!/bin/bash
# Test if API is accessible
echo "Testing API connection..."
echo ""

# Test if API server is responding
echo "1. Testing API health..."
curl -s http://localhost:8000/docs > /dev/null && echo "✅ API docs accessible" || echo "❌ API docs not accessible"

echo ""
echo "2. Testing pipelines endpoint..."
curl -s -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/pipelines | head -c 100 && echo "..." || echo "❌ Pipelines endpoint failed"

echo ""
echo "3. Testing policies endpoint..."
curl -s -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/policies | head -c 100 && echo "..." || echo "❌ Policies endpoint failed"

echo ""
echo "✅ API connection test complete"

