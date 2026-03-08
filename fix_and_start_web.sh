#!/bin/bash
# Fix common web app issues and start it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${SCRIPT_DIR}/apps/web"

echo "🔧 Fixing and Starting Web App"
echo "================================"
echo ""

# Try to activate nvm if it exists
if [ -d "$HOME/.nvm" ]; then
    echo "📦 Activating nvm..."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
fi

# Try to add Homebrew node to PATH if it exists
if [ -d "/usr/local/opt/node/bin" ]; then
    export PATH="/usr/local/opt/node/bin:$PATH"
fi
if [ -d "/opt/homebrew/opt/node/bin" ]; then
    export PATH="/opt/homebrew/opt/node/bin:$PATH"
fi

# Check for Node.js/npm
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not in PATH"
    echo ""
    echo "Node.js is installed but not activated. Try:"
    echo "  1. source ~/.nvm/nvm.sh  (if using nvm)"
    echo "  2. Or add to PATH: export PATH=\"/usr/local/opt/node/bin:\$PATH\""
    echo ""
    echo "Then run this script again."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not in PATH"
    echo ""
    echo "npm should come with Node.js. Try:"
    echo "  1. source ~/.nvm/nvm.sh  (if using nvm)"
    echo "  2. Or add to PATH: export PATH=\"/usr/local/opt/node/bin:\$PATH\""
    exit 1
fi

echo "✅ Node.js: $(node --version)"
echo "✅ npm: $(npm --version)"
echo ""

cd "$WEB_DIR" || exit 1

# Kill any existing process on port 3050
if lsof -Pi :3050 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🛑 Killing existing process on port 3050..."
    lsof -ti :3050 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Clear any build cache
echo "🧹 Clearing build cache..."
rm -rf node_modules/.vite 2>/dev/null
rm -rf dist 2>/dev/null
echo "✅ Cache cleared"

# Check if .env file exists and has correct API URL
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000/api/v1
EOF
    echo "✅ Created .env file"
else
    echo "✅ .env file exists"
    # Check if it has the API URL
    if ! grep -q "VITE_API_URL" .env; then
        echo "📝 Adding VITE_API_URL to .env..."
        echo "VITE_API_URL=http://localhost:8000/api/v1" >> .env
    fi
fi

echo ""
echo "🚀 Starting Vite dev server..."
echo "   Web app will be available at: http://localhost:3050"
echo "   API proxy: http://localhost:8000/api/v1"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

# Start the dev server
npm run dev

