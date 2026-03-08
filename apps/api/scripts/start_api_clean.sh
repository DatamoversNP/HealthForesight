#!/bin/bash
# Start API server with clean Python cache
cd "$(dirname "$0")/../../.."

# Clear Python cache
find apps/api/src -name "*.pyc" -delete 2>/dev/null
find apps/api/src -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Set environment
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
export LOG_LEVEL=INFO

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start server WITHOUT reload to avoid cache issues
uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000

