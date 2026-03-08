#!/bin/bash
# Start MAIN PLATFORM (not marketing website) on port 3050

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting HealthForesight MAIN PLATFORM"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Ensure index.html points to main.tsx (main platform)
echo "🔧 Step 1: Ensuring index.html points to main platform..."
WEB_DIR="$SCRIPT_DIR/apps/web"

if grep -q "main-marketing.tsx" "$WEB_DIR/index.html"; then
    echo "  ⚠️  index.html is pointing to marketing site. Fixing..."
    sed -i '' 's/main-marketing\.tsx/main.tsx/g' "$WEB_DIR/index.html"
    echo "  ✅ Fixed! index.html now points to main platform"
elif grep -q "main.tsx" "$WEB_DIR/index.html"; then
    echo "  ✅ index.html correctly points to main platform"
else
    echo "  ⚠️  Warning: Could not determine index.html configuration"
fi
echo ""

# Step 2: Stop all servers
echo "🛑 Step 2: Stopping existing servers..."
PORTS=(3050 3051 3052 8000)
for PORT in "${PORTS[@]}"; do
    if lsof -ti:$PORT > /dev/null 2>&1; then
        lsof -ti:$PORT | xargs kill -9 2>/dev/null && echo "  ✓ Stopped port $PORT" || true
    fi
done
sleep 3
echo ""

# Step 3: Start API Server
echo "🌐 Step 3: Starting API server..."

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "  ❌ Virtual environment not found!"
    exit 1
fi

# Set PYTHONPATH
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
echo ""

# Step 4: Start Web Server (MAIN PLATFORM)
echo "🖥️  Step 4: Starting MAIN PLATFORM web server on port 3050..."

cd "$WEB_DIR"

# Verify index.html points to main.tsx
if ! grep -q "main.tsx" "$WEB_DIR/index.html"; then
    echo "  ⚠️  Fixing index.html..."
    sed -i '' 's/main-marketing\.tsx/main.tsx/g' "$WEB_DIR/index.html"
fi

# Check node_modules
if [ ! -d "node_modules" ]; then
    echo "  📦 Installing npm dependencies..."
    npm install
fi

# Start web server (uses default vite.config.ts which serves index.html)
echo "  📝 Starting main platform application..."
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "  ✓ Web server started (PID: $WEB_PID)"

# Wait for Web
echo "  ⏳ Waiting for Web server..."
sleep 10
for i in {1..15}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "  ✅ Web server is ready!"
        break
    fi
    sleep 2
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ MAIN PLATFORM is UP and Running!"
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
echo "💡 Note: Port 3050 should now show the MAIN PLATFORM"
echo "   Marketing website runs on port 3052 (if needed)"
echo "   Documentation portal runs on port 3051 (if needed)"
echo ""
