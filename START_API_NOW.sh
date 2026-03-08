#!/bin/bash
# Start API Server - USE THIS FROM PROJECT ROOT

# Make sure we're in project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting API Server"
echo "📁 Working directory: $(pwd)"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "   Create it with: python3 -m venv .venv"
    exit 1
fi

# Set PYTHONPATH with ABSOLUTE paths
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

echo "📝 PYTHONPATH: $PYTHONPATH"
echo ""

# Verify module can be found
echo "🔍 Verifying module can be imported..."
python3 -c "import uepi_api; print('✅ uepi_api module found!')" || {
    echo "❌ Error: uepi_api module not found!"
    echo ""
    echo "Checking structure..."
    ls -la apps/api/src/ 2>/dev/null || echo "apps/api/src not found"
    exit 1
}

echo ""

# Stop existing server
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🛑 Stopping existing API server..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Change to src directory (this is important!)
cd apps/api/src

echo "🌐 Starting API server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Start server
python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000
