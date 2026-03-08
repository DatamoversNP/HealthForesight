#!/bin/bash
# Start Local Development Environment (No Azure Required)

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting HealthForesight - Local Development"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ensure we're using local storage (not Azure)
export STORAGE_PATH="./data"
export USE_AZURE_FILE_STORAGE="false"

echo "✅ Configuration:"
echo "   - Storage: Local file storage (./data)"
echo "   - Azure: Disabled"
echo "   - Environment: Development"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/apps/api/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Ensure data directory exists
echo "📁 Ensuring data directory exists..."
mkdir -p "$SCRIPT_DIR/data"
echo "✅ Data directory ready"

# Stop any existing servers
echo ""
echo "🛑 Stopping any existing servers..."

if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   Stopping API server on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -ti:3050 > /dev/null 2>&1; then
    echo "   Stopping Web server on port 3050..."
    lsof -ti:3050 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 Starting API Server..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd apps/api/src

# Start API server in background
nohup python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    > "$SCRIPT_DIR/api-server.log" 2>&1 &

API_PID=$!
echo "✅ API server started (PID: $API_PID)"
echo "   Waiting for API to be ready..."
sleep 5

# Check if API is responding
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is responding!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  API may still be starting. Check logs: tail -f $SCRIPT_DIR/api-server.log"
    else
        sleep 2
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🖥️  Starting Web Server..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd "$SCRIPT_DIR/apps/web"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    echo "✅ npm dependencies installed"
fi

# Start web server in background
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "✅ Web server started (PID: $WEB_PID)"
echo "   Waiting for Web server to be ready..."
sleep 8

# Check if Web server is responding
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "✅ Web server is responding!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  Web server may still be starting. Check logs: tail -f $SCRIPT_DIR/web-server.log"
    else
        sleep 2
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SUCCESS! Application is running locally!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Web Application: http://localhost:3050"
echo "🔧 API Server:      http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   API:  tail -f $SCRIPT_DIR/api-server.log"
echo "   Web:  tail -f $SCRIPT_DIR/web-server.log"
echo ""
echo "🛑 To stop:"
echo "   pkill -f 'uvicorn uepi_api.main:app'"
echo "   pkill -f 'vite'"
echo ""
echo "═══════════════════════════════════════════════════════════════"
