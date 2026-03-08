#!/bin/bash
# Start API server with correct PYTHONPATH

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"

echo "🚀 Starting API Server"
echo ""

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "📦 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Set PYTHONPATH correctly
# uepi_api is in apps/api/src/uepi_api
# uepi_common is in packages/common/src/uepi_common
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

echo "📝 PYTHONPATH: $PYTHONPATH"
echo ""

# Verify module can be imported
echo "🔍 Verifying imports..."
python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR/apps/api/src'); import uepi_api; print('✅ uepi_api module found')" || {
    echo "❌ Error: uepi_api module not found"
    echo ""
    echo "Checking structure..."
    ls -la "$SCRIPT_DIR/apps/api/src/" || echo "src directory not found"
    exit 1
}

echo ""

# Stop existing server
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping existing API server..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Change to API directory
cd "$API_DIR"

echo "🌐 Starting API server on port 8000..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Start API server
python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000
