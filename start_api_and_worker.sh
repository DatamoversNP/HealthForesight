#!/bin/bash
# Start API, Celery worker, or frontend (run each in a separate terminal)
# Usage:
#   ./start_api_and_worker.sh          # prints commands for all three
#   ./start_api_and_worker.sh api      # start API only (port 8000)
#   ./start_api_and_worker.sh worker   # start Celery worker (needs Redis)
#   ./start_api_and_worker.sh web     # start frontend only (port 3050)

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

API_DIR="$SCRIPT_DIR/apps/api"
WORKER_DIR="$SCRIPT_DIR/apps/worker"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHONPATH_API="$API_DIR/src:$SCRIPT_DIR/packages/common/src"
PYTHONPATH_WORKER="$WORKER_DIR/src:$SCRIPT_DIR/packages/common/src:$API_DIR/src"

start_api() {
  # Free port 8000 if something is already using it
  if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Stopping existing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
  fi
  export PYTHONPATH="$PYTHONPATH_API:$PYTHONPATH"
  if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
  fi
  echo "Starting API on http://localhost:8000 ..."
  cd "$API_DIR/src"
  exec python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
}

start_worker() {
  export PYTHONPATH="$PYTHONPATH_WORKER:$PYTHONPATH"
  if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
  fi
  if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is not running. Start Redis first:"
    echo "  macOS: brew services start redis"
    echo "  Or: redis-server"
    exit 1
  fi
  echo "Starting Celery worker..."
  cd "$WORKER_DIR"
  exec celery -A uepi_worker.main.app worker --loglevel=info
}

start_web() {
  # Ensure npm is in PATH (e.g. when using nvm, fnm, or homebrew)
  if ! command -v npm >/dev/null 2>&1; then
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    [ -s "$HOME/.fnm/fnm" ] && eval "$("$HOME/.fnm/fnm" env)"
    [ -f "$HOME/.zshrc" ] && . "$HOME/.zshrc"
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Install Node.js from https://nodejs.org or run from a terminal where 'npm' works."
    echo "If you use nvm, run: nvm use default (or install node first)."
    exit 1
  fi
  if [ ! -d "$SCRIPT_DIR/apps/web/node_modules" ]; then
    echo "Installing frontend dependencies (npm install)..."
    (cd "$SCRIPT_DIR/apps/web" && npm install)
  fi
  echo "Starting frontend on http://localhost:3050 ..."
  echo "  (API should be at http://localhost:8000)"
  cd "$SCRIPT_DIR/apps/web"
  exec npm run dev
}

case "${1:-}" in
  api)
    start_api
    ;;
  worker)
    start_worker
    ;;
  web)
    start_web
    ;;
  *)
    echo "Start API, worker, and frontend (use three terminals)."
    echo ""
    echo "Terminal 1 - API:"
    echo "  $SCRIPT_DIR/start_api_and_worker.sh api"
    echo ""
    echo "Terminal 2 - Celery worker (requires Redis):"
    echo "  $SCRIPT_DIR/start_api_and_worker.sh worker"
    echo ""
    echo "Terminal 3 - Frontend (then open http://localhost:3050):"
    echo "  $SCRIPT_DIR/start_api_and_worker.sh web"
    echo ""
    exit 0
    ;;
esac
