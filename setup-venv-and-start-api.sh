#!/bin/bash

# Setup script that creates a virtual environment and starts the API
# This is the cleanest approach for macOS

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 Setting up Virtual Environment and Starting API"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"
echo ""

# Install packages
echo "📦 Installing Python packages..."
echo "   This will take 2-3 minutes on first run..."
echo ""
pip install --quiet --upgrade pip
pip install --quiet fastapi "uvicorn[standard]" "pydantic[email]" pydantic-settings "python-jose[cryptography]" httpx boto3 sqlalchemy polars pyarrow pandas prometheus-client python-multipart email-validator cryptography scipy numpy
echo "✅ Packages installed"
echo ""

# Stop any existing API server
echo "🛑 Stopping any existing API server..."
PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$PID" ]; then
    kill $PID 2>/dev/null || true
    sleep 1
    if lsof -ti:8000 > /dev/null 2>&1; then
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    echo "✅ Stopped existing server"
else
    echo "ℹ️  No existing server found"
fi
echo ""

# Copy policies file
if [ ! -f "/tmp/policies_00000000-0000-0000-0000-000000000002.json" ]; then
    echo "📋 Copying policies file..."
    if [ -f "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" ]; then
        cp "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" "/tmp/policies_00000000-0000-0000-0000-000000000002.json"
        echo "✅ Policies file copied"
    fi
    echo ""
fi

# Start API server
echo "🚀 Starting API server..."
cd "$API_DIR"

# Set PYTHONPATH
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Start in background
nohup python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/api-server.log" 2>&1 &

NEW_PID=$!
sleep 4

# Check if running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ API server started (PID: $NEW_PID)"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "🎉 SUCCESS! API is Running!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "🌐 API: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"
    echo "💼 Frontend: http://localhost:3050/policies"
    echo ""
    echo "To stop: ./stop-api.sh"
    echo "To restart: ./setup-venv-and-start-api.sh"
    echo "═══════════════════════════════════════════════════════════════"
else
    echo "❌ API server failed to start"
    echo "Check logs: tail -f $SCRIPT_DIR/api-server.log"
    exit 1
fi
