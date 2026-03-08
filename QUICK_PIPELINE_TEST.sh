#!/bin/bash
# Quick test to see if pipelines are loading in API

echo "🔍 Quick Pipeline Test"
echo "====================="
echo ""

# Test API
echo "Testing API endpoint..."
RESPONSE=$(curl -s http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" 2>&1)

# Check if we got a valid response
if echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(f'✅ Found {len(d)} pipelines')" 2>/dev/null; then
    COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; print(len(d))" 2>/dev/null || echo "0")
    
    if [ "$COUNT" -gt 0 ]; then
        echo ""
        echo "📋 Sample pipelines:"
        echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin) if sys.stdin.read(1) else []; [print(f'   - {p.get(\"pipeline_name\") or p.get(\"name\")}') for p in d[:5]]" 2>/dev/null
        echo ""
        echo "✅ Pipelines are loading correctly!"
    else
        echo ""
        echo "⚠️  API returned 0 pipelines"
        echo ""
        echo "💡 Solution: Restart API server"
        echo "   1. Stop current API (CTRL+C)"
        echo "   2. Run: ./START_API_NOW.sh"
        echo "   3. Wait for server to start"
        echo "   4. Run this test again"
    fi
else
    echo "❌ API call failed"
    echo "   Response: ${RESPONSE:0:200}"
    echo ""
    echo "💡 Check if API is running:"
    echo "   curl http://localhost:8000/api/v1/me"
fi
