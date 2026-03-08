#!/bin/bash
# Start the web server on port 3050

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🌐 Starting Web Server on Port 3050"
echo "═══════════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEB_DIR="$SCRIPT_DIR/apps/web"

# Load nvm first (if available)
if [ -d "$HOME/.nvm" ]; then
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    echo "✅ Loaded nvm from $NVM_DIR"
fi

# Try to source shell profile to get npm in PATH (for homebrew, etc.)
if [ -f ~/.zshrc ]; then
    source ~/.zshrc 2>/dev/null || true
fi
if [ -f ~/.bash_profile ]; then
    source ~/.bash_profile 2>/dev/null || true
fi
if [ -f ~/.profile ]; then
    source ~/.profile 2>/dev/null || true
fi

# Check for npm in common locations
if ! command -v npm &> /dev/null; then
    # Try common npm locations
    if [ -f /usr/local/bin/npm ]; then
        export PATH="/usr/local/bin:$PATH"
    fi
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found!"
    echo ""
    
    # Check if nvm is available but Node.js not installed
    if [ -d "$HOME/.nvm" ] && [ -s "$NVM_DIR/nvm.sh" ]; then
        echo "📦 nvm is installed but Node.js is not. Installing Node.js LTS..."
        nvm install --lts
        nvm use --lts
        nvm alias default lts/*
        
        # Reload nvm
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        
        if command -v npm &> /dev/null; then
            echo "✅ Node.js installed successfully!"
        else
            echo "❌ Installation failed. Please install manually:"
            echo "   Run: ./INSTALL_NODE_AND_START_WEB.sh"
            exit 1
        fi
    else
        echo "Please install Node.js and npm:"
        echo "  1. Run: ./INSTALL_NODE_AND_START_WEB.sh (uses nvm)"
        echo "  2. Or visit https://nodejs.org/ and download LTS version"
        echo "  3. Or use Homebrew: brew install node"
        echo ""
        exit 1
    fi
fi

echo "✅ Found npm: $(which npm)"
echo "   Node version: $(node --version 2>/dev/null || echo 'unknown')"
echo "   npm version: $(npm --version 2>/dev/null || echo 'unknown')"
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
