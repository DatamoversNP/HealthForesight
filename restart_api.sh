#!/bin/bash
# Restart API server

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"

echo "============================================================"
echo "RESTART API SERVER"
echo "============================================================"
echo ""

# Step 1: Stop existing server
echo "🛑 Stopping existing API server..."

# Kill processes by port
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    echo "   ✅ Stopped server on port 8000"
    sleep 2
else
    echo "   ⚠️  No server on port 8000"
fi

# Kill by process name
API_PIDS=$(ps aux | grep -E "uvicorn.*main:app|python.*uvicorn.*main" | grep -v grep | awk '{print $2}' || true)
if [ -n "$API_PIDS" ]; then
    echo "$API_PIDS" | xargs kill -9 2>/dev/null || true
    echo "   ✅ Stopped uvicorn processes"
    sleep 1
fi

echo ""

# Step 2: Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "📦 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Continuing anyway..."
fi

# Step 3: Set PYTHONPATH
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Step 4: Start server
echo ""
echo "🚀 Starting API server on port 8000..."
cd "$API_DIR/src"

echo "   API will be available at: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

# Start server (foreground so user can see output)
python3 -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000
