#!/bin/bash
# Start API Server with correct Python path
cd "$(dirname "$0")"
PROJECT_ROOT="$(cd ../.. && pwd)"
export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src:${PYTHONPATH}"
python3 -m uvicorn uepi_api.main:app --reload --port 8000
