#!/usr/bin/env bash
# Run from project root: ./run_setup_from_here.sh
# Installs Celery for API, runs migrations, then reminds you to restart API + worker.

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== 1. Install API dependency (Celery) ==="
if [ -d ".venv" ]; then
  .venv/bin/pip install 'celery[redis]'
elif command -v poetry &>/dev/null; then
  cd apps/api && poetry install && cd "$ROOT"
else
  echo "Using system/default pip..."
  pip install 'celery[redis]'
fi

echo ""
echo "=== 2. Run Alembic migrations (apps/api) ==="
cd "$ROOT/apps/api"
if [ -d "$ROOT/.venv" ]; then
  "$ROOT/.venv/bin/alembic" upgrade head
else
  alembic upgrade head
fi
cd "$ROOT"

echo ""
echo "=== Done ==="
echo "Next: restart API and start the worker (in separate terminals):"
echo "  ./restart_api_now.sh"
echo "  ./start_api_and_worker.sh worker"
echo "(Ensure Redis is running: redis-cli ping)"
