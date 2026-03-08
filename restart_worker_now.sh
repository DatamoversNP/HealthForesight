#!/bin/bash
# Stop any running Celery worker, then start the worker (foreground).
# Usage: ./restart_worker_now.sh
# Requires Redis to be running (e.g. brew services start redis).

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Stopping any running Celery worker..."
pkill -f "celery.*uepi_worker.main.app" 2>/dev/null || true
sleep 2

WORKER_DIR="$SCRIPT_DIR/apps/worker"
API_DIR="$SCRIPT_DIR/apps/api"
VENV_DIR="$SCRIPT_DIR/.venv"
export PYTHONPATH="$WORKER_DIR/src:$SCRIPT_DIR/packages/common/src:$API_DIR/src:$PYTHONPATH"
if [ -d "$VENV_DIR" ]; then
  source "$VENV_DIR/bin/activate"
fi

if ! redis-cli ping >/dev/null 2>&1; then
  echo "Redis is not running. Start Redis first:"
  echo "  macOS: brew services start redis"
  echo "  Or: redis-server"
  exit 1
fi

echo "Starting Celery worker..."
echo "  (API should be at http://localhost:8000; worker processes analysis jobs)"
echo ""
cd "$WORKER_DIR"
exec celery -A uepi_worker.main.app worker --loglevel=info
