#!/bin/bash
# Check if API server is running and provide instructions

echo "🔍 Checking API server status..."
echo ""

# Check if port 8000 is in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ Port 8000 is in use"
    echo ""
    
    # Try to check if it's actually the API server
    if curl -s --max-time 2 http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ API server is running and responding!"
        echo ""
        echo "You can proceed with observation analysis:"
        echo "  ./run-observation-analysis-only.sh"
    else
        echo "⚠️  Port 8000 is in use but API server is not responding"
        echo ""
        echo "To free up the port, run:"
        echo "  lsof -ti:8000 | xargs kill -9"
        echo ""
        echo "Then start the API server:"
        echo "  ./start-api-server.sh"
    fi
else
    echo "❌ API server is not running"
    echo ""
    echo "Start it with:"
    echo "  ./start-api-server.sh"
fi
