#!/bin/bash
# Script to start API and fix observations

set -e

echo "================================================================================"
echo "START API AND FIX OBSERVATIONS"
echo "================================================================================"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "Step 1: Starting API server..."
echo ""

cd apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"

# Check if API is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is already running"
else
    echo "Starting API server in background..."
    nohup python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/api_server.log 2>&1 &
    API_PID=$!
    echo "API server started with PID: $API_PID"
    echo "Waiting for API to be ready..."
    
    # Wait for API to be ready (max 30 seconds)
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
fi

# Verify API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API failed to start. Check /tmp/api_server.log for errors"
    exit 1
fi

echo ""
echo "Step 2: Running diagnostic..."
echo ""

cd "$SCRIPT_DIR"
python3 scripts/diagnose_observation_data.py

echo ""
echo "Step 3: Creating observations from claims data..."
echo ""

python3 scripts/create_observations_from_claims_data.py

echo ""
echo "================================================================================"
echo "DONE!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Check the UI at http://localhost:3050 to see observations"
echo "2. If observations still show N/A, check:"
echo "   - API logs: tail -f /tmp/api_server.log"
echo "   - Claims data exists: ls -lh apps/data/target_data_model/*/CLAIMS_LINES/"
echo "   - Analysis results have treatment_post: Check database or API"
echo ""
echo "To stop the API server:"
echo "  pkill -f 'uvicorn uepi_api.main:app'"
echo ""
