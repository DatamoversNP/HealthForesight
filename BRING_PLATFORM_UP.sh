#!/bin/bash
# Bring up the main HealthForesight platform on port 3050

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"
WEB_DIR="$SCRIPT_DIR/apps/web"

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Bringing HealthForesight Main Platform Up"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Stop all processes on ports 3050, 3051, 3052, 8000
echo "🛑 Step 1: Stopping all existing processes..."

PORTS=(3050 3051 3052 8000)
for PORT in "${PORTS[@]}"; do
    if lsof -ti:$PORT > /dev/null 2>&1; then
        echo "   Stopping process on port $PORT..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    fi
done
sleep 3
echo "   ✅ All ports cleared"
echo ""

# Step 2: Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "📦 Step 2: Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "   ✅ Virtual environment activated"
    echo ""
fi

# Step 3: Start API Server
echo "🌐 Step 3: Starting API server on port 8000..."
cd "$API_DIR"
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

nohup python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    > "$SCRIPT_DIR/api-server.log" 2>&1 &

API_PID=$!
echo "   ✅ API server started (PID: $API_PID)"

# Wait for API
echo "   ⏳ Waiting for API to be ready..."
sleep 5
for i in {1..15}; do
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ API server is responding!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ⚠️  API server may still be starting. Check: tail -f $SCRIPT_DIR/api-server.log"
    else
        sleep 2
    fi
done
echo ""

# Step 4: Start MAIN Web Server (port 3050) - using default vite.config.ts
echo "🖥️  Step 4: Starting MAIN Web server on port 3050..."
cd "$WEB_DIR"

# Ensure node_modules
if [ ! -d "node_modules" ]; then
    echo "   📦 Installing npm dependencies..."
    npm install
fi

# Start main app (npm run dev uses vite.config.ts which runs on port 3050)
echo "   📝 Starting main platform application..."
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "   ✅ Web server started (PID: $WEB_PID)"

# Wait for Web
echo "   ⏳ Waiting for Web server to be ready..."
sleep 10
for i in {1..15}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "   ✅ Web server is responding!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ⚠️  Web server may still be starting. Check: tail -f $SCRIPT_DIR/web-server.log"
    else
        sleep 2
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Platform is UP and Running!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Main Platform:   http://localhost:3050"
echo "🔧 API Server:      http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo "❤️  API Health:      http://localhost:8000/health"
echo ""
echo "📝 View Logs:"
echo "   API: tail -f $SCRIPT_DIR/api-server.log"
echo "   Web: tail -f $SCRIPT_DIR/web-server.log"
echo ""
echo "🛑 To Stop:"
echo "   lsof -ti:8000 | xargs kill -9"
echo "   lsof -ti:3050 | xargs kill -9"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 Note: Port 3050 should show the MAIN PLATFORM (not marketing website)"
echo "   Marketing website runs on port 3052"
echo "   Documentation portal runs on port 3051"
echo ""
