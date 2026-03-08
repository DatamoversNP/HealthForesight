#!/bin/bash
# Start API server with proper setup

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"

echo "🚀 Starting API Server (Fixed)"
echo ""

# Kill existing
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping existing server..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Activate venv
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

# Set PYTHONPATH
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Start server
cd "$API_DIR/src"
echo "🌐 Starting on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
