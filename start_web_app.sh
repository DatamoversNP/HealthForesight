#!/bin/bash
# Start the web application with proper error handling
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${SCRIPT_DIR}/apps/web"

cd "$WEB_DIR" || exit 1

echo "🌐 Starting UEPI Web Application..."
echo "📝 Will be available at http://localhost:3050"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if port 3050 is already in use
if lsof -Pi :3050 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3050 is already in use"
    echo "   Trying to kill existing process..."
    lsof -ti :3050 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start the dev server
echo "🚀 Starting Vite dev server..."
echo "   Press Ctrl+C to stop"
echo ""

npm run dev
