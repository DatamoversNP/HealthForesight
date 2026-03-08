#!/bin/bash

# Script to restart API server in the background
# This version runs the API in the background and returns control to you

echo "🔄 Restarting API Server in background..."
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
echo "🚀 Starting API server in background..."
echo "📍 Directory: $API_DIR"
echo "🌐 URL: http://localhost:8000"
echo "📝 Logs: $SCRIPT_DIR/api-server.log"
echo ""

# Change to API directory
cd "$API_DIR"

# Set PYTHONPATH to include the src directory so Python can find uepi_api
export PYTHONPATH="$API_DIR/src:$PYTHONPATH"

# Also need to add packages/common to PYTHONPATH
COMMON_DIR="$SCRIPT_DIR/packages/common/src"
export PYTHONPATH="$COMMON_DIR:$PYTHONPATH"

# Start uvicorn in the background and redirect output to log file
nohup uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/api-server.log" 2>&1 &

NEW_PID=$!
echo "✅ API server started (PID: $NEW_PID)"
echo ""
echo "To stop the server, run: kill $NEW_PID"
echo "Or use: ./stop-api.sh"
echo ""
echo "To view logs: tail -f $SCRIPT_DIR/api-server.log"
