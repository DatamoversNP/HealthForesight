#!/bin/bash
# Startup script for Azure App Service (Linux)
# Use absolute paths and PORT. Log to stderr so output appears in Azure log stream.

WWWROOT="${WWWROOT:-/home/site/wwwroot}"
cd "$WWWROOT" || exit 1

# Absolute paths for PYTHONPATH
SRC_DIR="$WWWROOT/src"
COMMON_DIR="$WWWROOT/packages/common/src"

if [ ! -d "$SRC_DIR/uepi_api" ]; then
  FOUND=$(find "$WWWROOT" -maxdepth 4 -type d -name "uepi_api" 2>/dev/null | head -1)
  if [ -n "$FOUND" ]; then
    SRC_DIR=$(dirname "$FOUND")
    COMMON_DIR=$(find "$WWWROOT" -maxdepth 4 -type d -path "*/packages/common/src" 2>/dev/null | head -1)
    [ -z "$COMMON_DIR" ] && COMMON_DIR="$WWWROOT/packages/common/src"
  fi
fi

if [ ! -d "$SRC_DIR/uepi_api" ]; then
  echo "ERROR: uepi_api not found under $WWWROOT" >&2
  ls -la "$WWWROOT" >&2
  exit 1
fi

export PYTHONPATH="$SRC_DIR:$COMMON_DIR"
cd "$SRC_DIR" || exit 1

# Prefer Oryx venv (created when SCM_DO_BUILD_DURING_DEPLOYMENT=true)
if [ -f "$WWWROOT/antenv/bin/python" ]; then
  PYTHON_CMD="$WWWROOT/antenv/bin/python"
elif [ -f "$WWWROOT/antenv/bin/python3" ]; then
  PYTHON_CMD="$WWWROOT/antenv/bin/python3"
else
  PYTHON_CMD="python3"
  echo "WARN: No antenv; using system python. Set SCM_DO_BUILD_DURING_DEPLOYMENT=true and redeploy." >&2
fi

PORT="${PORT:-8000}"
echo "Starting uvicorn port=$PORT PYTHONPATH=$PYTHONPATH" >&2
exec "$PYTHON_CMD" -m uvicorn uepi_api.main:app --host 0.0.0.0 --port "$PORT"
