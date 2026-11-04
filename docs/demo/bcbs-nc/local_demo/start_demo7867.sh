#!/usr/bin/env bash
# Data Voyager local demo stack on ports 7867+
#   7867 = API
#   7868 = Web (Data Voyager branding)
#   7870 = Redis (docker uepi-demo-redis)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"
mkdir -p logs docs/demo/bcbs-nc/local_demo

ENV_FILE="$ROOT/.env.demo7867"
VENV="$ROOT/.venv7867"
PIDDIR="$ROOT/docs/demo/bcbs-nc/local_demo"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — create it with Azure DATABASE_URL first."
  exit 1
fi
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Missing $VENV — recreate with python3.14 -m venv .venv7867 && pip install deps"
  exit 1
fi

# Redis on 7870
if ! docker ps --format '{{.Names}}' | grep -q '^uepi-demo-redis$'; then
  docker rm -f uepi-demo-redis >/dev/null 2>&1 || true
  docker run -d --name uepi-demo-redis -p 7870:6379 redis:7-alpine >/dev/null
  echo "Started redis on 7870"
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:7870/0}"

kill_port() {
  local p="$1"
  if lsof -ti:"$p" >/dev/null 2>&1; then
    lsof -ti:"$p" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

kill_port 7867
kill_port 7868

export PYTHONPATH="$ROOT/apps/api/src:$ROOT/packages/common/src"
nohup "$VENV/bin/python" -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 7867 \
  >"$ROOT/logs/demo7867_api.log" 2>&1 &
echo $! >"$PIDDIR/api.pid"
echo "API pid $(cat "$PIDDIR/api.pid") → http://127.0.0.1:7867"

export PYTHONPATH="$ROOT/apps/worker/src:$ROOT/packages/common/src:$ROOT/apps/api/src"
nohup "$VENV/bin/celery" -A uepi_worker.main.app worker --loglevel=info \
  >"$ROOT/logs/demo7867_worker.log" 2>&1 &
echo $! >"$PIDDIR/worker.pid"
echo "Worker pid $(cat "$PIDDIR/worker.pid")"

# Web env + vite config expected to already exist; recreate if missing
WEB_ENV="$ROOT/apps/web/.env.development.local"
if [[ ! -f "$WEB_ENV" ]]; then
  cat >"$WEB_ENV" <<'EOF'
VITE_API_URL=/api/v1
VITE_APP_NAME="Data Voyager"
VITE_APP_BYLINE=
VITE_LOGO_SRC=/brands/data-voyager/logo-color.png
VITE_LOGO_ICON_SRC=/brands/data-voyager/logo-color-icon.png
VITE_LOGO_ON_DARK_SRC=/brands/data-voyager/logo-reversed.png
VITE_FAVICON=/brands/data-voyager/logo-color-icon.png
VITE_APP_BAR_FULL_LOGO=true
EOF
fi

cd "$ROOT/apps/web"
nohup npm run dev -- --config vite.config.demo7867.ts --port 7868 --host 0.0.0.0 \
  >"$ROOT/logs/demo7867_web.log" 2>&1 &
echo $! >"$PIDDIR/web.pid"
echo "Web pid $(cat "$PIDDIR/web.pid") → http://127.0.0.1:7868"

# Wait for health
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:7867/api/v1/health >/dev/null && curl -sf http://127.0.0.1:7868/ >/dev/null; then
    echo "READY"
    echo "  UI:  http://localhost:7868"
    echo "  API: http://localhost:7867/docs"
    exit 0
  fi
  sleep 1
done
echo "Started but health check timed out — see logs/demo7867_*.log"
exit 1
