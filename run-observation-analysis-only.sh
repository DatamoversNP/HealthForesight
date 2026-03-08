#!/bin/bash
# Run observation analysis only (assuming data is already loaded)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "🔍 Running Observation Analysis Only"
echo ""

# Check if API server is running
if ! curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  API server is not running!"
    echo ""
    echo "Please start the API server first:"
    echo "  ./start-api-server.sh"
    echo ""
    echo "Or in a separate terminal:"
    echo "  cd '$SCRIPT_DIR'"
    echo "  source .venv/bin/activate"
    echo "  export PYTHONPATH=\"\$(pwd)/apps/api/src:\$(pwd)/packages/common/src:\$PYTHONPATH\""
    echo "  python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    exit 1
fi

echo "✅ API server is running"
echo ""

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Run the observation analysis Python script
cd "$SCRIPT_DIR"
python3 scripts/run_observation_analysis_only.py
