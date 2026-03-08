#!/bin/bash
# Check status of both servers

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "=========================================="
echo "Server Status"
echo "=========================================="
echo ""

# Check API Server
echo "📡 API Server (port 8000):"
if [ -f "$LOGS_DIR/api.pid" ]; then
    API_PID=$(cat "$LOGS_DIR/api.pid")
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "  ✅ Running (PID: $API_PID)"
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "  ✅ Health check: OK"
        else
            echo "  ⚠️  Health check: Failed (server may be starting)"
        fi
    else
        echo "  ❌ Not running (stale PID file)"
        rm "$LOGS_DIR/api.pid"
    fi
else
    LSOF_PID=$(lsof -ti:8000 2>/dev/null)
    if [ ! -z "$LSOF_PID" ]; then
        echo "  ✅ Running (PID: $LSOF_PID, no PID file)"
    else
        echo "  ❌ Not running"
    fi
fi

echo ""

# Check Frontend Server
echo "🌐 Frontend Server (port 3050):"
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "  ✅ Running (PID: $FRONTEND_PID)"
        if curl -s http://localhost:3050 > /dev/null 2>&1; then
            echo "  ✅ Server responding"
        else
            echo "  ⚠️  Server not responding (may be starting)"
        fi
    else
        echo "  ❌ Not running (stale PID file)"
        rm "$LOGS_DIR/frontend.pid"
    fi
else
    LSOF_PID=$(lsof -ti:3050 2>/dev/null)
    if [ ! -z "$LSOF_PID" ]; then
        echo "  ✅ Running (PID: $LSOF_PID, no PID file)"
    else
        echo "  ❌ Not running"
    fi
fi

echo ""
echo "=========================================="
echo "Log Files:"
echo "  API:      $LOGS_DIR/api.log"
echo "  Frontend: $LOGS_DIR/frontend.log"
echo "=========================================="

