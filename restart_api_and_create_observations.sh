#!/bin/bash
# Restart API server and create all observations

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_DIR="$SCRIPT_DIR/apps/api"

echo "============================================================"
echo "RESTART API SERVER AND CREATE ALL OBSERVATIONS"
echo "============================================================"
echo ""

# Step 1: Find and stop existing API server
echo "🛑 Step 1: Stopping existing API server..."
API_PIDS=$(ps aux | grep -E "uvicorn|fastapi|python.*main.py|python.*api" | grep -v grep | awk '{print $2}' || true)

if [ -n "$API_PIDS" ]; then
    echo "   Found API server processes: $API_PIDS"
    echo "$API_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "   ✅ Stopped"
else
    echo "   ⚠️  No API server process found (might already be stopped)"
fi

# Step 2: Check if port 8000 is in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   ⚠️  Port 8000 still in use, killing processes..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo ""

# Step 3: Start API server
echo "🚀 Step 2: Starting API server..."
cd "$API_DIR"

# Activate virtual environment
VENV_DIR="$SCRIPT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

# Set PYTHONPATH
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Start server in background
echo "   Starting server on port 8000..."
cd "$API_DIR/src"
nohup python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/api_server.log 2>&1 &
API_PID=$!

echo "   ✅ API server starting (PID: $API_PID)"
echo "   Log: tail -f /tmp/api_server.log"

# Step 4: Wait for server to be ready
echo ""
echo "⏳ Step 3: Waiting for server to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1 || \
       curl -s http://localhost:8000/docs > /dev/null 2>&1 || \
       curl -s http://localhost:8000/api/v1/policies -H "Authorization: Bearer dev-token-123" > /dev/null 2>&1; then
        echo "   ✅ Server is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Waiting... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "   ⚠️  Server might not be ready yet, but continuing..."
fi

echo ""

# Step 5: Create all observations
echo "🎯 Step 4: Creating all observations..."
echo ""

response=$(curl -s -X POST "http://localhost:8000/api/v1/observations/create-all-from-pending-analyses" \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json")

if echo "$response" | grep -q "observations_created"; then
    echo "✅ SUCCESS!"
    echo ""
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "🎉 All observations created!"
    echo "   Refresh the web page to see them!"
elif echo "$response" | grep -q "Method Not Allowed\|404\|405"; then
    echo "❌ Endpoint not found - trying individual creation..."
    echo ""
    cd "$SCRIPT_DIR/apps/api"
    python3 scripts/create_all_observations_final.py
else
    echo "Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
fi

echo ""
echo "============================================================"
echo "✅ DONE!"
echo "============================================================"
echo ""
echo "API Server: Running (PID: $API_PID)"
echo "Log: tail -f /tmp/api_server.log"
echo ""
echo "🌐 Refresh the web page to see observations!"
