#!/bin/bash
# Test if API server can start successfully

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔍 Testing API server import..."
echo ""

# Activate venv
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Test import
if python3 -c "from uepi_api.main import app; print('✅ App imported successfully!')"; then
    echo ""
    echo "✅ API server can start!"
    echo ""
    echo "Now you can start it with:"
    echo "  cd apps/api/src"
    echo "  python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "Or use: ./START_API_SERVER.sh"
else
    echo ""
    echo "❌ API server cannot start - check errors above"
    exit 1
fi
