#!/bin/bash
# Start API in the background

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting API in Background"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if API is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  API is already running on port 8000"
    echo "   Process ID: $(lsof -ti:8000 | head -1)"
    echo ""
    read -p "Stop existing API and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing API..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "Keeping existing API running."
        exit 0
    fi
fi

# Check if we're in the right directory
if [ ! -d "apps/api" ]; then
    echo "❌ Error: apps/api directory not found"
    echo "   Please run this script from the project root"
    exit 1
fi

# Set environment variables
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:$PYTHONPATH"
export STORAGE_PATH="${PWD}/data"

echo "✅ STORAGE_PATH: $STORAGE_PATH"
echo "✅ PYTHONPATH: $PYTHONPATH"
echo ""

# Navigate to API directory for venv
cd apps/api

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Go back to project root
cd ../..

# Create log file
LOG_FILE="logs/api_startup.log"
mkdir -p logs
echo "Starting API at $(date)" > "$LOG_FILE"

# Start API in background
echo "🚀 Starting API server in background..."
echo "   Logs: $LOG_FILE"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

nohup python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
API_PID=$!

echo "✅ API started (PID: $API_PID)"
echo ""
echo "Waiting 10 seconds for startup..."
sleep 10

# Check if API is running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ API is running successfully!"
    echo ""
    echo "To stop the API:"
    echo "   kill $API_PID"
    echo "   or: lsof -ti:8000 | xargs kill -9"
    echo ""
    echo "To view logs:"
    echo "   tail -f $LOG_FILE"
    echo "   or: ./view_logs.sh api"
else
    echo "❌ API failed to start. Check logs:"
    echo "   tail -f $LOG_FILE"
    exit 1
fi

