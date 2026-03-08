#!/bin/bash
# Stop both API and Web servers

echo "🛑 Stopping both servers..."

# Stop API server
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   Stopping API server on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "   ✅ API server stopped"
else
    echo "   ℹ️  No API server running"
fi

# Stop Web server
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "   Stopping Web server on port 3050..."
    lsof -ti:3050 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "   ✅ Web server stopped"
else
    echo "   ℹ️  No Web server running"
fi

echo ""
echo "✅ Both servers stopped!"
