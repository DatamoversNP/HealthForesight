#!/bin/bash

# Simple script to stop the API server
# Usage: ./stop-api.sh

echo "🛑 Stopping API Server..."
echo ""

# Find process on port 8000
PID=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found API server (PID: $PID)"
    echo "Stopping..."
    kill $PID 2>/dev/null
    sleep 2
    
    # Force kill if still running
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "Force stopping..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "❌ Failed to stop API server"
        exit 1
    else
        echo "✅ API server stopped"
    fi
else
    echo "ℹ️  No API server found running on port 8000"
fi
