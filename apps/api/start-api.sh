#!/bin/bash
# Start API server from api directory (convenience script)

# Get the project root (parent of apps directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
VENV_DIR="$PROJECT_ROOT/.venv"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Run ./start-both-servers.sh first to set up the environment"
    exit 1
fi

# Set Python path with ABSOLUTE paths
export PYTHONPATH="$PROJECT_ROOT/apps/api/src:$PROJECT_ROOT/packages/common/src:$PYTHONPATH"

echo "🚀 Starting API server..."
echo "   Project root: $PROJECT_ROOT"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# Change to src directory (important for module resolution)
cd "$PROJECT_ROOT/apps/api/src"

# Start server from src directory
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
