#!/bin/bash
# Start Main Platform (not marketing or docs) on port 3050

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"
WEB_DIR="$SCRIPT_DIR/apps/web"

echo "🚀 Starting HealthForesight Main Platform"
echo "=========================================="
echo ""

# Stop any existing processes
echo "🛑 Stopping existing servers..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped API server" || echo "  ℹ️  No API server"
lsof -ti:3050 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped Web server" || echo "  ℹ️  No Web server"
sleep 2

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "📦 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Start API Server (port 8000)
echo ""
echo "🌐 Starting API server on port 8000..."
cd "$API_DIR"
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

nohup python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    > "$SCRIPT_DIR/api-server.log" 2>&1 &

API_PID=$!
echo "  ✓ API server started (PID: $API_PID)"

# Wait for API
echo "  ⏳ Waiting for API server..."
sleep 5
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✅ API server is ready!"
        break
    fi
    sleep 2
done

# Start Web Server (port 3050) - MAIN PLATFORM
echo ""
echo "🖥️  Starting MAIN Web server on port 3050..."
cd "$WEB_DIR"

# Ensure node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing npm dependencies..."
    npm install
fi

# Start main web app (NOT marketing, NOT docs) - uses default vite.config.ts
echo "  📝 Starting main platform (vite.config.ts)..."
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "  ✓ Web server started (PID: $WEB_PID)"

# Wait for Web
echo "  ⏳ Waiting for Web server..."
sleep 8
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "  ✅ Web server is ready!"
        break
    fi
    sleep 2
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Main Platform is running!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Main Platform:   http://localhost:3050"
echo "🔧 API Server:      http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   API:  tail -f $SCRIPT_DIR/api-server.log"
echo "   Web:  tail -f $SCRIPT_DIR/web-server.log"
echo ""
echo "🛑 To stop:"
echo "   lsof -ti:8000 | xargs kill -9"
echo "   lsof -ti:3050 | xargs kill -9"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
