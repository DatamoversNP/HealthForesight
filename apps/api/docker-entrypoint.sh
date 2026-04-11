#!/bin/sh
set -e
export PYTHONUNBUFFERED=1
# App Service "Application settings" often override Dockerfile ENV. If PYTHONPATH is wrong or empty,
# ``uepi_common`` (under /app/packages/common/src) never loads → create_app() fails → degraded ping only.
export PYTHONPATH="/app/apps/api/src:/app/packages/common/src:/app/apps/worker/src"
# Azure Linux custom containers: platform forwards to the port in the PORT env var.
# WEBSITES_PORT tells Azure which port your app uses; PORT is what many runtimes must bind to.
# Prefer PORT first (Azure-injected), then WEBSITES_PORT (app setting), then 8080.
LISTEN="${PORT:-${WEBSITES_PORT:-8080}}"
echo "healthforesight-api: binding 0.0.0.0:${LISTEN} (PORT=${PORT:-unset} WEBSITES_PORT=${WEBSITES_PORT:-unset} WEBSITE_HOSTNAME=${WEBSITE_HOSTNAME:-unset})"
# Gunicorn + Uvicorn worker: more reliable process supervision on App Service than raw uvicorn.
exec gunicorn uepi_api.main:app \
  --pythonpath /app/apps/api/src \
  --pythonpath /app/packages/common/src \
  --pythonpath /app/apps/worker/src \
  -k uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${LISTEN}" \
  --workers 1 \
  --timeout 600 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance
