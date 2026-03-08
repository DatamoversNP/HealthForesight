#!/bin/bash

# Simple script to restart the API server
# Usage: ./restart-api.sh
# Or double-click it in Finder (after making it executable)

echo "🔄 Restarting API Server..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_DIR="$SCRIPT_DIR/apps/api"

# Check if API directory exists
if [ ! -d "$API_DIR" ]; then
    echo "❌ Error: API directory not found at $API_DIR"
    exit 1
fi

# Find and kill any existing API server processes
echo "🔍 Checking for running API server on port 8000..."
PID=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "🛑 Stopping existing API server (PID: $PID)..."
    kill $PID 2>/dev/null
    sleep 2
    
    # Force kill if still running
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "⚠️  Force stopping..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    echo "✅ Stopped"
else
    echo "ℹ️  No API server found running on port 8000"
fi

echo ""
echo "🚀 Starting API server..."
echo "📍 Directory: $API_DIR"
echo "🌐 URL: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "════════════════════════════════════════════════"
echo ""

# Change to API directory and start the server
cd "$API_DIR"

# Set PYTHONPATH to include the src directory so Python can find uepi_api
export PYTHONPATH="$API_DIR/src:$PYTHONPATH"

# Also need to add packages/common to PYTHONPATH
COMMON_DIR="$SCRIPT_DIR/packages/common/src"
export PYTHONPATH="$COMMON_DIR:$PYTHONPATH"

# Start uvicorn with auto-reload
exec uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
