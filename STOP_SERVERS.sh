#!/bin/bash
# Stop both servers

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "=========================================="
echo "Stopping Servers"
echo "=========================================="
echo ""

# Stop API Server
if [ -f "$LOGS_DIR/api.pid" ]; then
    API_PID=$(cat "$LOGS_DIR/api.pid")
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "🛑 Stopping API Server (PID: $API_PID)..."
        kill $API_PID
        rm "$LOGS_DIR/api.pid"
        echo "✅ API Server stopped"
    else
        echo "⚠️  API Server not running (PID file exists but process not found)"
        rm "$LOGS_DIR/api.pid"
    fi
else
    # Try to find and kill by port
    echo "🔍 Looking for API Server on port 8000..."
    LSOF_PID=$(lsof -ti:8000 2>/dev/null)
    if [ ! -z "$LSOF_PID" ]; then
        echo "🛑 Stopping API Server (PID: $LSOF_PID)..."
        kill $LSOF_PID
        echo "✅ API Server stopped"
    else
        echo "ℹ️  API Server not running"
    fi
fi

echo ""

# Stop Frontend Server
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 Stopping Frontend Server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm "$LOGS_DIR/frontend.pid"
        echo "✅ Frontend Server stopped"
    else
        echo "⚠️  Frontend Server not running (PID file exists but process not found)"
        rm "$LOGS_DIR/frontend.pid"
    fi
else
    # Try to find and kill by port
    echo "🔍 Looking for Frontend Server on port 3050..."
    LSOF_PID=$(lsof -ti:3050 2>/dev/null)
    if [ ! -z "$LSOF_PID" ]; then
        echo "🛑 Stopping Frontend Server (PID: $LSOF_PID)..."
        kill $LSOF_PID
        echo "✅ Frontend Server stopped"
    else
        echo "ℹ️  Frontend Server not running"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Done"
echo "=========================================="

