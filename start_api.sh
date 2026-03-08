#!/bin/bash
# Start the API server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use"
    PID=$(lsof -ti :8000)
    echo "   Process ID: $PID"
    echo "   Run: kill -9 $PID to free the port"
    exit 1
fi

# Set environment
export PYTHONPATH="${SCRIPT_DIR}/apps/api/src:${SCRIPT_DIR}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
export LOG_LEVEL=INFO

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "⚠️  Virtual environment not found at .venv"
fi

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Please install dependencies:"
    echo "   pip install -r apps/api/requirements.txt"
    exit 1
fi

echo "🚀 Starting UEPI API Server"
echo "=============================="
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   API: http://localhost:8000/api/v1"
echo ""
echo "   Press CTRL+C to stop the server"
echo ""

# Start the server
uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
