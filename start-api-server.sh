#!/bin/bash
# Start API server with correct Python path

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

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
