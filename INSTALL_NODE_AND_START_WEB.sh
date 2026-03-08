#!/bin/bash
# Install Node.js using nvm and start the web server

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "📦 Installing Node.js and Starting Web Server"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEB_DIR="$SCRIPT_DIR/apps/web"

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Check if nvm is loaded
if ! command -v nvm &> /dev/null && [ -s "$NVM_DIR/nvm.sh" ]; then
    echo "📥 Loading nvm..."
    source "$NVM_DIR/nvm.sh"
fi

# Check if Node.js is installed via nvm
if ! command -v node &> /dev/null; then
    echo "📦 Node.js not found. Installing Node.js LTS via nvm..."
    nvm install --lts
    nvm use --lts
    nvm alias default lts/*
    echo "✅ Node.js installed"
else
    echo "✅ Node.js found: $(node --version)"
    echo "✅ npm found: $(npm --version)"
fi

# Ensure we're using the latest LTS
echo ""
echo "🔄 Ensuring LTS version is active..."
nvm use --lts 2>/dev/null || nvm install --lts

echo ""
echo "✅ Node.js: $(node --version)"
echo "✅ npm: $(npm --version)"
echo ""

# Check if port 3050 is in use
if lsof -ti:3050 > /dev/null 2>&1; then
    echo "⚠️  Port 3050 is already in use"
    echo "   Stopping existing process..."
    lsof -ti:3050 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Navigate to web directory
cd "$WEB_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "🚀 Starting Vite dev server on port 3050..."
echo "   Access at: http://localhost:3050"
echo ""

# Start the server
npm run dev

