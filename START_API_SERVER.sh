#!/bin/bash
# Start API Server - Fixed version with correct Python path

PROJECT_ROOT="/Users/nilesh/Downloads/uepi-migration-20260123-151729"
cd "$PROJECT_ROOT/apps/api"

# Set Python path to include both src directory and common package
export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src:${PYTHONPATH}"

# Start the server
python3 -m uvicorn uepi_api.main:app --reload --port 8000
