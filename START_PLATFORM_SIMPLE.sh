#!/bin/bash
# Simple script to start the entire platform
# Run this from anywhere - it will find the project directory

# Find project root (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting HealthForesight Platform"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 Project directory: $(pwd)"
echo ""

# Step 1: Stop existing servers
echo "🛑 Step 1: Stopping existing servers..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped API server" || echo "  ℹ️  No API server"
lsof -ti:3050 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Stopped Web server" || echo "  ℹ️  No Web server"
sleep 2

# Step 2: Start API Server
echo ""
echo "🌐 Step 2: Starting API server..."

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "  ❌ Virtual environment not found!"
    echo "     Create it with: python3 -m venv .venv"
    exit 1
fi

# Set PYTHONPATH with absolute paths
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Start API in background
cd apps/api/src
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

# Step 3: Start Web Server
echo ""
echo "🖥️  Step 3: Starting Web server..."

cd "$SCRIPT_DIR/apps/web"

# Check node_modules
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing npm dependencies..."
    npm install
fi

# Start web in background
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
echo "✅ Platform is UP and Running!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Main Platform:   http://localhost:3050"
echo "🔧 API Server:      http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo ""
echo "📝 View Logs:"
echo "   API: tail -f api-server.log"
echo "   Web: tail -f web-server.log"
echo ""
echo "🛑 To Stop:"
echo "   lsof -ti:8000 | xargs kill -9"
echo "   lsof -ti:3050 | xargs kill -9"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
