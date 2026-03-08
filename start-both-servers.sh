#!/bin/bash
# Complete startup script - starts both API and Web servers with all dependencies

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Starting HealthForesight Application"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
API_DIR="$SCRIPT_DIR/apps/api"
WEB_DIR="$SCRIPT_DIR/apps/web"

# ============================================================================
# STEP 1: Setup Python Virtual Environment and Dependencies
# ============================================================================
echo "📦 Step 1: Setting up Python environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "   ✅ Virtual environment created"
fi

echo "   Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "   ✅ Virtual environment activated"

echo "   Installing Python packages (this may take 2-3 minutes)..."
pip install --quiet --upgrade pip
pip install --quiet \
    fastapi \
    "uvicorn[standard]" \
    "pydantic[email]" \
    pydantic-settings \
    "python-jose[cryptography]" \
    httpx \
    boto3 \
    sqlalchemy \
    polars \
    pyarrow \
    pandas \
    prometheus-client \
    python-multipart \
    email-validator \
    cryptography \
    scipy \
    numpy \
    scikit-learn \
    statsmodels

echo "   ✅ Python packages installed"
echo ""

# ============================================================================
# STEP 2: Stop Any Existing Servers
# ============================================================================
echo "🛑 Step 2: Stopping any existing servers..."

# Stop API server on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   Stopping API server on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "   ✅ API server stopped"
else
    echo "   ℹ️  No API server running on port 8000"
fi

# Stop Web server on port 3050
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "   Stopping Web server on port 3050..."
    lsof -ti:3050 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "   ✅ Web server stopped"
else
    echo "   ℹ️  No Web server running on port 3050"
fi

echo ""

# ============================================================================
# STEP 3: Copy Required Data Files
# ============================================================================
if [ ! -f "/tmp/policies_00000000-0000-0000-0000-000000000002.json" ]; then
    echo "📋 Step 3: Copying data files..."
    if [ -f "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" ]; then
        cp "$SCRIPT_DIR/data/policies_00000000-0000-0000-0000-000000000002.json" \
           "/tmp/policies_00000000-0000-0000-0000-000000000002.json"
        echo "   ✅ Data files copied"
    fi
    echo ""
fi

# ============================================================================
# STEP 4: Start API Server
# ============================================================================
echo "🌐 Step 4: Starting API server..."

cd "$API_DIR"
export PYTHONPATH="$API_DIR/src:$SCRIPT_DIR/packages/common/src:$PYTHONPATH"

# Start API server in background
nohup python -m uvicorn uepi_api.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    > "$SCRIPT_DIR/api-server.log" 2>&1 &

API_PID=$!
echo "   Started API server (PID: $API_PID)"
echo "   Waiting for API server to start..."
sleep 5

# Check if API server started successfully
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ API server is responding!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ⚠️  API server may still be starting. Check logs: tail -f $SCRIPT_DIR/api-server.log"
    else
        sleep 2
    fi
done

echo ""

# ============================================================================
# STEP 5: Start Web Server
# ============================================================================
echo "🖥️  Step 5: Starting Web server..."

cd "$WEB_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing npm dependencies..."
    npm install
    echo "   ✅ npm dependencies installed"
fi

# Start web server in background
nohup npm run dev > "$SCRIPT_DIR/web-server.log" 2>&1 &

WEB_PID=$!
echo "   Started Web server (PID: $WEB_PID)"
echo "   Waiting for Web server to start..."
sleep 8

# Check if Web server started successfully
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:3050 > /dev/null 2>&1; then
        echo "   ✅ Web server is responding!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ⚠️  Web server may still be starting. Check logs: tail -f $SCRIPT_DIR/web-server.log"
    else
        sleep 2
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ SUCCESS! Both servers are starting!"
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
echo "   ./stop-both-servers.sh"
echo ""
echo "═══════════════════════════════════════════════════════════════"
