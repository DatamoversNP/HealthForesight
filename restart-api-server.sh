#!/bin/bash
# Kill any process on port 8000 and restart API server

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "🔄 Restarting API Server"
echo ""

# Kill any process on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "✅ Port 8000 freed"
    echo ""
fi

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Run ./start-both-servers.sh first to set up the environment"
    exit 1
fi

# Set Python path
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

echo "🚀 Starting API server..."
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# Change to project root and run uvicorn
cd "$SCRIPT_DIR"
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
