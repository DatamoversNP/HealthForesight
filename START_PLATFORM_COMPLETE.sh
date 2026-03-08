#!/bin/bash
# Complete script to start MAIN PLATFORM with API and Web servers

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting HealthForesight MAIN PLATFORM"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 Project directory: $(pwd)"
echo ""

# Step 1: Ensure index.html points to main platform (not marketing)
echo "🔧 Step 1: Ensuring index.html points to main platform..."
WEB_DIR="$SCRIPT_DIR/apps/web"

if grep -q "main-marketing.tsx" "$WEB_DIR/index.html"; then
    echo "  ⚠️  Fixing index.html..."
    sed -i '' 's/main-marketing\.tsx/main.tsx/g' "$WEB_DIR/index.html"
    echo "  ✅ Fixed! index.html now points to main platform"
elif grep -q "main.tsx" "$WEB_DIR/index.html"; then
    echo "  ✅ index.html correctly points to main platform"
fi
echo ""

# Step 2: Stop all existing servers
echo "🛑 Step 2: Stopping existing servers..."
PORTS=(3050 3051 3052 8000)
for PORT in "${PORTS[@]}"; do
    if lsof -ti:$PORT > /dev/null 2>&1; then
        lsof -ti:$PORT | xargs kill -9 2>/dev/null && echo "  ✓ Stopped port $PORT" || true
    fi
done
sleep 3
echo ""

# Step 3: Activate virtual environment
if [ -d ".venv" ]; then
    echo "📦 Step 3: Activating virtual environment..."
    source .venv/bin/activate
    echo "  ✅ Virtual environment activated"
else
    echo "  ❌ Virtual environment not found!"
    echo "     Create it with: python3 -m venv .venv"
    exit 1
fi
echo ""

# Step 4: Start API Server
echo "🌐 Step 4: Starting API server on port 8000..."

# Set PYTHONPATH
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Verify module
python3 -c "import uepi_api; print('  ✅ Module found')" || {
    echo "  ❌ Error: uepi_api module not found!"
    exit 1
}

# Start API in background
cd apps/api/src
nohup python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    > "$SCRIPT_DIR/api-server.log" 2>&1 &

API_PID=$!
echo "  ✓ API server started (PID: $API_PID)"

# Wait for API to be ready
echo "  ⏳ Waiting for API server..."
sleep 5
for i in {1..15}; do
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✅ API server is responding!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "  ⚠️  API server may still be starting. Check: tail -f api-server.log"
    else
        sleep 2
    fi
done
echo ""

# Step 5: Start Web Server (MAIN PLATFORM)
echo "🖥️  Step 5: Starting MAIN PLATFORM web server on port 3050..."

cd "$WEB_DIR"

# Verify index.html
if ! grep -q "main.tsx" "$WEB_DIR/index.html" || grep -q "main-marketing.tsx" "$WEB_DIR/index.html"; then
    echo "  ⚠️  Fixing index.html..."
    sed -i '' 's/main-marketing\.tsx/main.tsx/g' "$WEB_DIR/index.html"
fi

# Check node_modules
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing npm dependencies..."
    npm install
fi

# Start web server
echo "  📝 Starting main platform application..."
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "  ✓ Web server started (PID: $WEB_PID)"

# Wait for Web to be ready
echo "  ⏳ Waiting for Web server..."
sleep 10
for i in {1..15}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "  ✅ Web server is responding!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "  ⚠️  Web server may still be starting. Check: tail -f web-server.log"
    else
        sleep 2
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ MAIN PLATFORM is UP and Running!"
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
echo "💡 Verify:"
echo "   - Port 3050 should show MAIN PLATFORM (not marketing)"
echo "   - Port 8000 should respond with API health check"
echo "   - If errors, check logs above"
echo ""
