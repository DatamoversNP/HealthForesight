#!/bin/bash

# Complete setup and start script for API server
# This script will:
# 1. Check if Python dependencies are installed
# 2. Install them if needed
# 3. Start the API server

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 API Server Setup and Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_DIR="$SCRIPT_DIR/apps/api"
COMMON_DIR="$SCRIPT_DIR/packages/common/src"

# Check Python
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found: $($PYTHON_CMD --version)"
echo ""

# Function to check if package is installed
check_package() {
    $PYTHON_CMD -c "import $1" 2>/dev/null
}

# List of required packages
REQUIRED_PACKAGES=("fastapi" "uvicorn" "pydantic" "pydantic_settings")

# Check which packages are missing
MISSING_PACKAGES=()
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    import_name=${pkg//-/_}  # Convert fastapi to fastapi, pydantic-settings to pydantic_settings
    if ! check_package "$import_name"; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

# Install missing packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "📦 Installing missing Python packages..."
    echo "   Missing: ${MISSING_PACKAGES[*]}"
    echo "   This may take a few minutes..."
    echo ""
    
    # Install packages
    $PYTHON_CMD -m pip install --user --quiet "${MISSING_PACKAGES[@]}" uvicorn[standard] python-jose httpx boto3 2>&1 | grep -v "Requirement already satisfied" | grep -E "(Installing|Successfully|ERROR|WARNING)" || true
    
    echo ""
    echo "✅ Package installation complete"
    echo ""
else
    echo "✅ All required packages are already installed"
    echo ""
fi

# Stop any existing API server
echo "🛑 Stopping any existing API server..."
PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$PID" ]; then
    kill $PID 2>/dev/null || true
    sleep 1
    # Force kill if still running
    if lsof -ti:8000 > /dev/null 2>&1; then
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    echo "✅ Stopped existing server"
else
    echo "ℹ️  No existing server found"
fi
echo ""

# Verify packages are available
echo "🔍 Verifying installation..."
if ! check_package "fastapi"; then
    echo "❌ FastAPI still not available. Please install manually:"
    echo "   python3 -m pip install --user fastapi uvicorn[standard] pydantic pydantic-settings python-jose httpx boto3"
    exit 1
fi
echo "✅ Packages verified"
echo ""

# Check if policies file exists
if [ ! -f "/tmp/policies_00000000-0000-0000-0000-000000000002.json" ]; then
    echo "📋 Copying policies file to /tmp..."
    if [ -f "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" ]; then
        mkdir -p /tmp
        cp "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" "/tmp/policies_00000000-0000-0000-0000-000000000002.json"
        echo "✅ Policies file copied"
    else
        echo "⚠️  Warning: Policies file not found (API will still start)"
    fi
    echo ""
fi

# Start API server
echo "🚀 Starting API server..."
echo "📍 Directory: $API_DIR"
echo "🌐 URL: http://localhost:8000"
echo "📝 Logs: $SCRIPT_DIR/api-server.log"
echo ""

cd "$API_DIR"

# Set PYTHONPATH
export PYTHONPATH="$API_DIR/src:$COMMON_DIR:$PYTHONPATH"

# Start in background
nohup $PYTHON_CMD -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/api-server.log" 2>&1 &

NEW_PID=$!
sleep 3

# Check if it's running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ API server started successfully (PID: $NEW_PID)"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "🎉 Setup Complete!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "API is running at: http://localhost:8000"
    echo "API docs at: http://localhost:8000/docs"
    echo ""
    echo "To stop: ./stop-api.sh"
    echo "To view logs: tail -f api-server.log"
    echo ""
    echo "Now go to: http://localhost:3050/policies"
    echo "═══════════════════════════════════════════════════════════════"
else
    echo "❌ API server failed to start"
    echo "Check logs: tail -f $SCRIPT_DIR/api-server.log"
    exit 1
fi
