#!/bin/bash
# Quick restart script for API server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 Stopping API server..."

# Stop API server on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "✅ API server stopped"
else
    echo "ℹ️  No API server running on port 8000"
fi

echo ""
echo "🚀 Starting API server..."

# Use start-api-server.sh if it exists, otherwise start directly
if [ -f "./start-api-server.sh" ]; then
    ./start-api-server.sh
else
    echo "❌ start-api-server.sh not found"
    exit 1
fi
