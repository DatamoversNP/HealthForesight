#!/bin/bash
# Start Frontend Server
# Run this after starting the API server

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT/apps/web"

echo "=========================================="
echo "Starting Frontend Server"
echo "=========================================="
echo ""

# Try to load nvm if it exists
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "📦 Loading nvm..."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    # Try to use node version from .nvmrc if it exists
    if [ -f "$PROJECT_ROOT/.nvmrc" ]; then
        echo "📌 Using Node.js version from .nvmrc..."
        nvm use
    elif [ -f "$PROJECT_ROOT/apps/web/.nvmrc" ]; then
        echo "📌 Using Node.js version from apps/web/.nvmrc..."
        nvm use
    else
        # Use default or latest LTS
        echo "📌 Using default Node.js version..."
        nvm use default 2>/dev/null || nvm use node 2>/dev/null || nvm use --lts 2>/dev/null || true
    fi
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found."
    echo ""
    echo "Please install Node.js using one of these methods:"
    echo "  1. Using nvm: nvm install --lts && nvm use --lts"
    echo "  2. Download from: https://nodejs.org/"
    echo "  3. Using Homebrew: brew install node"
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

echo "🚀 Starting frontend server..."
echo ""
echo "Frontend will be available at: http://localhost:3050"
echo "API should be running at: http://localhost:8000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

npm run dev


