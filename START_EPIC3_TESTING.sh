#!/bin/bash
# Start servers for Epic 3 UI testing

echo "🚀 Starting servers for Epic 3 UI Testing..."
echo ""

# Check if API server is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ API server already running on port 8000"
else
    echo "📡 Starting API server..."
    cd "$(dirname "$0")"
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/apps/api/src:$(pwd)/packages/common/src"
    
    # Start API server in background
    cd apps/api/src
    python3 -m uvicorn uepi_api.main:app --reload --port 8000 > /tmp/uepi_api.log 2>&1 &
    API_PID=$!
    echo "   API server started (PID: $API_PID)"
    echo "   Logs: tail -f /tmp/uepi_api.log"
    echo "   Waiting for server to start..."
    sleep 3
fi

# Check if frontend is already running
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "✅ Frontend already running on port 3050"
else
    echo "🌐 Starting frontend..."
    cd "$(dirname "$0")/apps/web"
    
    # Start frontend in background
    npm run dev > /tmp/uepi_frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend started (PID: $FRONTEND_PID)"
    echo "   Logs: tail -f /tmp/uepi_frontend.log"
    echo "   Waiting for frontend to start..."
    sleep 5
fi

echo ""
echo "✅ Servers should be running!"
echo ""
echo "📋 Next Steps:"
echo "   1. Open browser: http://localhost:3050"
echo "   2. Navigate to Policies"
echo "   3. Click 'Open Workspace' on any policy"
echo "   4. Go to 'Decisions' tab (9th tab)"
echo "   5. Click 'Create Decision'"
echo "   6. Fill in form and create"
echo "   7. Go to 'Evidence' tab (10th tab)"
echo "   8. Click 'Link Evidence'"
echo ""
echo "📊 Check logs:"
echo "   API: tail -f /tmp/uepi_api.log"
echo "   Frontend: tail -f /tmp/uepi_frontend.log"
echo ""
echo "🛑 To stop servers:"
echo "   kill $API_PID $FRONTEND_PID"
echo "   OR: lsof -ti:8000 | xargs kill && lsof -ti:3050 | xargs kill"
echo ""


