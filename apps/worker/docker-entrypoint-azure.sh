#!/bin/sh
set -e
export PYTHONUNBUFFERED=1
LISTEN="${PORT:-${WEBSITES_PORT:-8080}}"
# Azure Linux Web Apps probe PORT; Celery has no HTTP listener — minimal health server in background.
if [ -n "${WEBSITE_SITE_NAME:-}" ] || [ -n "${WEBSITE_INSTANCE_ID:-}" ]; then
  echo "healthforesight-worker: Azure — health HTTP on 0.0.0.0:${LISTEN}, Celery foreground"
  python3 -m http.server "$LISTEN" --bind 0.0.0.0 --directory /tmp 2>/dev/null &
  HTTP_PID=$!
  trap 'kill "$HTTP_PID" 2>/dev/null; exit' INT TERM
fi
celery -A uepi_worker.main worker --loglevel="${CELERY_LOG_LEVEL:-info}"
CELERY_EXIT=$?
if [ -n "${HTTP_PID:-}" ]; then
  kill "$HTTP_PID" 2>/dev/null || true
fi
exit "$CELERY_EXIT"
