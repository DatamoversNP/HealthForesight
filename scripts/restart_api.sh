#!/bin/bash
# Restart the UEPI API server (stop existing, then start).
# Run from repo root: ./scripts/restart_api.sh
# Or from anywhere: /path/to/repo/scripts/restart_api.sh

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PORT="${PORT:-8000}"

echo "============================================================"
echo "RESTART API"
echo "============================================================"

# Stop by port
if command -v lsof >/dev/null 2>&1 && lsof -ti:"$PORT" >/dev/null 2>&1; then
    lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
    echo "   Stopped process on port $PORT"
    sleep 2
fi

# Stop any uvicorn running uepi_api.main
API_PIDS=$(ps aux 2>/dev/null | grep -E "uvicorn.*uepi_api\.main:app|uvicorn.*main:app" | grep -v grep | awk '{print $2}' || true)
if [ -n "$API_PIDS" ]; then
    echo "$API_PIDS" | xargs kill -9 2>/dev/null || true
    echo "   Stopped uvicorn processes"
    sleep 1
fi

# Paths
API_SRC="$REPO_ROOT/apps/api/src"
COMMON_SRC="$REPO_ROOT/packages/common/src"
export PYTHONPATH="$API_SRC:$COMMON_SRC:$PYTHONPATH"

# Optional venv
if [ -d "$REPO_ROOT/.venv" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
fi

echo ""
echo "Starting API on http://0.0.0.0:$PORT (docs: http://localhost:$PORT/docs)"
echo "Press Ctrl+C to stop."
echo ""

cd "$API_SRC"
exec python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port "$PORT"
