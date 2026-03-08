#!/bin/bash
# Start API Server with CORRECT PYTHONPATH

# From project root directory

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "🚀 Starting API Server"
echo ""

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "📦 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn[standard] pydantic pydantic-settings python-jose[cryptography] httpx boto3 polars pyarrow pandas
fi

# Set PYTHONPATH correctly
# uepi_api is at: apps/api/src/uepi_api/
# So PYTHONPATH must include: apps/api/src
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

echo "📝 PYTHONPATH: $PYTHONPATH"
echo ""

# Stop existing server
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping existing API server..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Change to API src directory
cd "$SCRIPT_DIR/apps/api/src"

echo "🌐 Starting API server on http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Start server (from src directory, so uepi_api.main is importable)
python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000
