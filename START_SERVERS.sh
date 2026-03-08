#!/bin/bash
# Start API and Frontend Servers
# Run this script to start both servers for testing

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Starting HealthForesight Servers"
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js"
    exit 1
fi

echo "Starting API Server on port 8000..."
echo "Terminal 1 - API Server:"
echo "  cd $PROJECT_ROOT/apps/api"
echo "  python3 -m uvicorn uepi_api.main:app --reload --port 8000"
echo ""
echo "Starting Frontend Server on port 3050..."
echo "Terminal 2 - Frontend:"
echo "  cd $PROJECT_ROOT/apps/web"
echo "  npm run dev"
echo ""
echo "=========================================="
echo "Or run in background:"
echo "=========================================="
echo ""
echo "API Server (background):"
echo "  cd $PROJECT_ROOT/apps/api && python3 -m uvicorn uepi_api.main:app --reload --port 8000 > /tmp/api.log 2>&1 &"
echo ""
echo "Frontend (background):"
echo "  cd $PROJECT_ROOT/apps/web && npm run dev > /tmp/frontend.log 2>&1 &"
echo ""
echo "Access application at: http://localhost:3050"
echo "API docs at: http://localhost:8000/docs"
echo ""


