#!/bin/bash
# Stop anything on port 8000, then start the API (foreground).
# Usage: ./restart_api_now.sh

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Stopping any process on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"
if [ -d "$SCRIPT_DIR/.venv" ]; then
  source "$SCRIPT_DIR/.venv/bin/activate"
fi

echo "Starting API on http://localhost:8000 ..."
echo "  Health: http://localhost:8000/health"
echo "  Docs:   http://localhost:8000/docs"
echo ""
cd "$SCRIPT_DIR/apps/api/src"
exec python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
