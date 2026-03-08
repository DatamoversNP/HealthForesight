#!/bin/bash
# Simple API server startup script
cd "$(dirname "$0")"

# Set environment
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
export LOG_LEVEL=INFO

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🚀 Starting UEPI API Server on http://0.0.0.0:8000"
echo "📝 API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000

