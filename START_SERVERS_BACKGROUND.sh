#!/bin/bash
# Start both servers in the background using nohup
# Servers will continue running even after you close the terminal

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Starting Servers in Background"
echo "=========================================="
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start API Server in background
echo "🚀 Starting API Server (port 8000)..."
cd "$PROJECT_ROOT/apps/api"
export PYTHONPATH="$PROJECT_ROOT/apps/api/src:$PROJECT_ROOT/packages/common/src:$PYTHONPATH"
nohup python3 -m uvicorn uepi_api.main:app --reload --port 8000 > "$PROJECT_ROOT/logs/api.log" 2>&1 &
API_PID=$!
echo "API Server started with PID: $API_PID"
echo "Logs: $PROJECT_ROOT/logs/api.log"
echo ""

# Start Frontend Server in background
echo "🚀 Starting Frontend Server (port 3050)..."
cd "$PROJECT_ROOT/apps/web"

# Source NVM if available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Use the default Node.js version
nvm use default || {
    echo "⚠️  Warning: Could not use nvm default. Using system Node.js."
}

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend Server started with PID: $FRONTEND_PID"
echo "Logs: $PROJECT_ROOT/logs/frontend.log"
echo ""

# Save PIDs to file for easy stopping
echo "$API_PID" > "$PROJECT_ROOT/logs/api.pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/logs/frontend.pid"

echo "=========================================="
echo "✅ Both servers are running in background"
echo "=========================================="
echo ""
echo "API Server:    http://localhost:8000"
echo "Frontend:      http://localhost:3050"
echo ""
echo "To view logs:"
echo "  tail -f $PROJECT_ROOT/logs/api.log"
echo "  tail -f $PROJECT_ROOT/logs/frontend.log"
echo ""
echo "To stop servers:"
echo "  ./STOP_SERVERS.sh"
echo ""
echo "To check server status:"
echo "  ./CHECK_SERVERS.sh"
echo ""

