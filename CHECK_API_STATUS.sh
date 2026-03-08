#!/bin/bash
# Quick script to check if API is running and responding

echo "🔍 Checking API Server Status..."
echo ""

# Check if port 8000 is in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ Port 8000 is in use"
    echo "   Process details:"
    lsof -i :8000 | grep LISTEN || echo "   (Port may be in use but not listening)"
else
    echo "❌ Port 8000 is not in use - API server is not running"
    exit 1
fi

echo ""
echo "🌐 Testing API health endpoint..."

# Test health endpoint
if curl -s --max-time 3 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo ""
    echo "Response:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "❌ API is not responding"
    echo ""
    echo "Possible issues:"
    echo "  1. Server is still starting (wait 10-20 seconds)"
    echo "  2. Server crashed (check terminal output)"
    echo "  3. Port conflict"
fi

echo ""
echo "📝 To view API logs, check the terminal where you ran START_API_NOW.sh"
